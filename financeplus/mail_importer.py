import email
import imaplib
import io
import json
import re
import time
from datetime import date, datetime
from email import policy
from email.utils import parseaddr
from pathlib import Path

from financeplus.db import insert_cliente, insert_documento, insert_mail, list_clienti
from financeplus.parsers import parse_report_pdf
from financeplus.storage import archive_uploaded_file

CONFIG_PATH = Path('data/mail_config.json')
PROCESSED_UIDS_PATH = Path('data/processed_mail_uids.json')
TEMP_DIR = Path('archive/_temporanea_da_classificare')

# Limiti anti OVERQUOTA Gmail IMAP.
# Gmail blocca temporaneamente IMAP quando riceve troppi comandi/fetch o troppi MB in poco tempo.
# Per questo l'app lavora a piccoli blocchi e memorizza gli UID gia elaborati.
DEFAULT_SAFE_LIMIT = 10
MAX_SAFE_LIMIT = 20
DEFAULT_SLEEP_SECONDS = 1.5

# Mittenti autorizzati: l'app scarica SOLO mail e allegati provenienti da questi indirizzi.
# Gli indirizzi sono normalizzati in minuscolo per evitare problemi con maiuscole/minuscole.
ALLOWED_SENDERS = tuple(addr.lower() for addr in (
    'elibetty731@gmail.com',
    'Valentinaboratto82@gmail.com',
    'stefano.faraone@eurofintechsrl.it',
    'praticheBS@proton.me',
    'sergio.pedolazzi@katudi.it',
    'paolo.baldinelli@katudi.it',
    'pratiche@katudi.it',
    'niccolo.sovico@ener2crowd.com',
))
CONFIG_PATH.parent.mkdir(exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class MemoryUpload:
    def __init__(self, name, data):
        self.name = name or 'allegato.bin'
        self._data = data or b''

    def getbuffer(self):
        return self._data

    def seek(self, *_):
        return None


def load_mail_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_mail_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')


def load_processed_uids(username='', mailbox='INBOX'):
    if PROCESSED_UIDS_PATH.exists():
        try:
            data = json.loads(PROCESSED_UIDS_PATH.read_text(encoding='utf-8'))
        except Exception:
            data = {}
    else:
        data = {}
    key = f'{username}|{mailbox}'
    return set(str(x) for x in data.get(key, []))


def save_processed_uids(uids, username='', mailbox='INBOX'):
    PROCESSED_UIDS_PATH.parent.mkdir(exist_ok=True)
    if PROCESSED_UIDS_PATH.exists():
        try:
            data = json.loads(PROCESSED_UIDS_PATH.read_text(encoding='utf-8'))
        except Exception:
            data = {}
    else:
        data = {}
    key = f'{username}|{mailbox}'
    # conserva al massimo 5000 UID per non far crescere troppo il file
    ordered = list(dict.fromkeys(str(x) for x in uids))[-5000:]
    data[key] = ordered
    PROCESSED_UIDS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def is_overquota_error(exc):
    txt = str(exc).upper()
    return 'OVERQUOTA' in txt or 'BANDWIDTH' in txt or 'TOO MANY' in txt


def gmail_raw_query(since_date=None, only_with_attachments=True):
    q = []
    if since_date:
        if isinstance(since_date, date):
            q.append('after:' + since_date.strftime('%Y/%m/%d'))
    if only_with_attachments:
        q.append('has:attachment')
    senders = ' OR '.join(f'from:{addr}' for addr in ALLOWED_SENDERS)
    q.append(f'({senders})')
    return ' '.join(q)


def decode_imap_error(prefix, status, data):
    detail = ''
    try:
        detail = ' '.join(x.decode('utf-8', errors='ignore') if isinstance(x, bytes) else str(x) for x in (data or []))
    except Exception:
        detail = str(data)
    return RuntimeError(f'{prefix}: {status} {detail}'.strip())


def clean(value):
    value = str(value or '').replace('\r', ' ').replace('\n', ' ')
    return re.sub(r'\s+', ' ', value).strip()


def sender_email(value):
    """Estrae solo l'indirizzo email dal campo From."""
    _, addr = parseaddr(str(value or ''))
    return clean(addr or value).lower()


def is_allowed_sender(value):
    return sender_email(value) in ALLOWED_SENDERS


def build_sender_search_criteria(since_date, sender):
    parts = []
    if since_date:
        parts.extend(['SINCE', f'"{imap_since(since_date)}"'])
    parts.extend(['FROM', f'"{sender}"'])
    return '(' + ' '.join(parts) + ')'


def search_allowed_sender_uids(imap, since_date=None, limit=DEFAULT_SAFE_LIMIT, only_with_attachments=True, already_processed=None):
    """Cerca su Gmail solo i messaggi dei mittenti autorizzati, in modalita anti-quota.

    Prima usa X-GM-RAW di Gmail: un solo comando IMAP invece di 8 ricerche separate.
    Se il server non lo supporta, usa il fallback per singolo mittente ma con limite rigido.
    """
    already_processed = already_processed or set()
    limit = max(1, min(int(limit or DEFAULT_SAFE_LIMIT), MAX_SAFE_LIMIT))
    all_uids = []

    raw_query = gmail_raw_query(since_date=since_date, only_with_attachments=only_with_attachments)
    try:
        status, data = imap.uid('search', None, 'X-GM-RAW', f'"{raw_query}"')
        if status == 'OK' and data and data[0]:
            all_uids = data[0].split()
        elif status not in ('OK', 'NO'):
            raise decode_imap_error('Errore ricerca Gmail X-GM-RAW', status, data)
    except Exception as exc:
        if is_overquota_error(exc):
            raise RuntimeError('Gmail ha bloccato temporaneamente IMAP per OVERQUOTA. Attendi 30-60 minuti e poi scarica un blocco da 5/10 mail.') from exc
        # Fallback conservativo: una ricerca per mittente, massimo pochi risultati per mittente.
        found = set()
        for sender in ALLOWED_SENDERS:
            criteria = build_sender_search_criteria(since_date, sender)
            status, data = imap.uid('search', None, criteria)
            if status == 'OK' and data and data[0]:
                found.update(data[0].split())
            elif status not in ('OK', 'NO'):
                raise decode_imap_error('Errore ricerca mittente', status, data)
            time.sleep(0.4)
        all_uids = list(found)

    def uid_key(uid):
        try:
            return int(uid)
        except Exception:
            return 0

    ordered = sorted(all_uids, key=uid_key, reverse=True)
    new_uids = []
    for uid in ordered:
        uid_s = uid.decode() if isinstance(uid, bytes) else str(uid)
        if uid_s in already_processed:
            continue
        new_uids.append(uid)
        if len(new_uids) >= limit:
            break
    return new_uids


def company_from_text(text):
    text = clean(text).upper()
    patterns = [
        r'([A-Z0-9 &\'\.\-]{3,90}\s+(?:S\.R\.L\.|SRL|S\.P\.A\.|SPA|S\.N\.C\.|SNC|S\.A\.S\.|SAS))',
        r'CLIENTE\s*[:\-]\s*([A-Z0-9 &\'\.\-]{3,90})',
        r'SOCIETA\s*[:\-]\s*([A-Z0-9 &\'\.\-]{3,90})',
        r'AZIENDA\s*[:\-]\s*([A-Z0-9 &\'\.\-]{3,90})',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return clean(m.group(1))[:120]
    return ''


def categoria_da_nome_file(filename):
    f = filename.lower()
    if 'visura' in f or 'camera' in f or 'cciaa' in f:
        return 'Visura'
    if 'centrale' in f or 'crif' in f or 'rischi' in f or 'banca' in f:
        return 'Centrale Rischi'
    if 'bilancio' in f or 'cee' in f or 'xbrl' in f:
        return 'Bilancio'
    if 'bozza' in f or 'provvisorio' in f:
        return 'Bozza Bilancio'
    if 'report' in f or 'rating' in f or 'cerved' in f or 'credit' in f:
        return 'Report'
    return 'Altro'


def find_or_create_cliente(denominazione, piva='', sede='', attivita='', pec='', amministratore='', sender=''):
    denominazione = clean(denominazione)
    piva = clean(piva)
    clienti = list_clienti()
    if not clienti.empty:
        for r in clienti.itertuples():
            if piva and str(getattr(r, 'piva', '') or '').strip() == piva:
                return int(r.id), False
            if denominazione and clean(getattr(r, 'denominazione', '')).upper() == denominazione.upper():
                return int(r.id), False
    if not denominazione:
        return 0, False
    cliente_id = insert_cliente(denominazione, piva, sede, attivita, pec, amministratore, '', sender)
    return cliente_id, True


def parse_attachment_pdf(filename, payload):
    if not filename.lower().endswith('.pdf'):
        return {}
    try:
        bio = io.BytesIO(payload)
        data, _ = parse_report_pdf(bio)
        return data or {}
    except Exception:
        return {}


def body_from_message(msg):
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and not part.get_filename():
                try:
                    body += part.get_content() + '\n'
                except Exception:
                    pass
    else:
        try:
            body = msg.get_content()
        except Exception:
            body = ''
    return clean(body)[:5000]


def save_temp_attachment(filename, payload, sender='', subject=''):
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[^A-Za-z0-9_. -]+', '_', filename or 'allegato.bin')
    path = TEMP_DIR / safe
    counter = 1
    while path.exists():
        path = TEMP_DIR / f'{counter}_{safe}'
        counter += 1
    path.write_bytes(payload or b'')
    note = TEMP_DIR / 'LEGGIMI_TEMPORANEI.txt'
    with open(note, 'a', encoding='utf-8') as fh:
        fh.write(f'File: {path.name} | Mittente: {sender} | Oggetto: {subject}\n')
    return str(path)


def imap_since(value):
    if isinstance(value, date):
        return value.strftime('%d-%b-%Y')
    return ''


def import_mail_attachments(config, since_date=None, limit=DEFAULT_SAFE_LIMIT, delete_after_save=False, only_new=True, only_with_attachments=True, sleep_seconds=DEFAULT_SLEEP_SECONDS):
    host = config.get('host', 'imap.gmail.com')
    port = int(config.get('port', 993))
    username = config.get('username', '')
    password = config.get('password', '')
    mailbox = config.get('mailbox', 'INBOX')

    if not username or not password:
        raise ValueError('Inserisci e salva prima email e password/app password.')

    # Blocco anti overquota: massimo 20 mail per ciclo.
    limit = max(1, min(int(limit or DEFAULT_SAFE_LIMIT), MAX_SAFE_LIMIT))
    sleep_seconds = max(0.0, float(sleep_seconds or 0))

    imap = imaplib.IMAP4_SSL(host, port)
    processed = load_processed_uids(username, mailbox) if only_new else set()
    processed_changed = False

    try:
        imap.login(username, password)
        imap.select(mailbox)

        # BLOCCO MITTENTI + ANTI-QUOTA:
        # scarica solo gli 8 mittenti autorizzati, solo allegati, solo UID non gia elaborati.
        uids = search_allowed_sender_uids(
            imap,
            since_date=since_date,
            limit=limit,
            only_with_attachments=only_with_attachments,
            already_processed=processed,
        )
        results = []

        for uid in uids:
            uid_s = uid.decode() if isinstance(uid, bytes) else str(uid)
            try:
                # BODY.PEEK evita di marcare la mail come letta. RFC822 serve per corpo e allegati.
                status, msg_data = imap.uid('fetch', uid, '(BODY.PEEK[])')
                if status != 'OK' or not msg_data or not msg_data[0]:
                    results.append({'uid': uid_s, 'stato': 'saltata_fetch_non_ok'})
                    continue

                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw, policy=policy.default)
                subject = clean(msg.get('subject', ''))
                sender = clean(msg.get('from', ''))
                sender_addr = sender_email(sender)

                # Secondo controllo di sicurezza: qualunque mittente non autorizzato viene scartato.
                if sender_addr not in ALLOWED_SENDERS:
                    processed.add(uid_s)
                    processed_changed = True
                    continue

                body = body_from_message(msg)
                mail_date = clean(msg.get('date', ''))

                attachment_names = []
                matched_cliente_id = 0
                created_cliente = False
                matched_name = company_from_text(subject + ' ' + body)
                matched_data = {}

                # Prima passata: leggo nomi allegati e, solo se PDF, provo estrazione dati cliente.
                for part in msg.iter_attachments():
                    filename = part.get_filename() or 'allegato.bin'
                    payload = part.get_payload(decode=True) or b''
                    attachment_names.append(filename)
                    pdf_data = parse_attachment_pdf(filename, payload)
                    if pdf_data.get('denominazione') or pdf_data.get('piva'):
                        matched_data = pdf_data
                        matched_name = pdf_data.get('denominazione') or matched_name
                        break

                matched_cliente_id, created_cliente = find_or_create_cliente(
                    matched_name,
                    piva=matched_data.get('piva', ''),
                    sede=matched_data.get('sede', ''),
                    attivita=matched_data.get('attivita', ''),
                    pec=matched_data.get('pec', ''),
                    amministratore=matched_data.get('amministratore', ''),
                    sender=sender,
                )

                insert_mail(matched_cliente_id, mail_date, 'Entrata', 'Scaricata', 'Sistema', sender, subject, body, ', '.join(attachment_names))

                saved_count = 0
                temp_count = 0
                for part in msg.iter_attachments():
                    filename = part.get_filename() or 'allegato.bin'
                    payload = part.get_payload(decode=True) or b''
                    if not payload:
                        continue
                    if matched_cliente_id:
                        upload = MemoryUpload(filename, payload)
                        categoria = categoria_da_nome_file(filename)
                        local_path, provider, cloud_id = archive_uploaded_file(matched_cliente_id, categoria, upload)
                        insert_documento(matched_cliente_id, categoria, filename, local_path, provider, cloud_id)
                        saved_count += 1
                    else:
                        save_temp_attachment(filename, payload, sender, subject)
                        temp_count += 1

                saved_successfully = bool(saved_count or temp_count or attachment_names)
                if delete_after_save and saved_successfully:
                    imap.uid('store', uid, '+FLAGS', r'(\Deleted)')

                processed.add(uid_s)
                processed_changed = True
                results.append({
                    'uid': uid_s,
                    'mittente': sender,
                    'oggetto': subject,
                    'cliente_id': matched_cliente_id,
                    'cliente_creato': created_cliente,
                    'cliente': matched_name,
                    'allegati_salvati': saved_count,
                    'temporanei': temp_count,
                    'mittente_autorizzato': sender_addr,
                    'eliminata_da_casella': bool(delete_after_save and saved_successfully),
                    'stato': 'salvata',
                })

                if sleep_seconds:
                    time.sleep(sleep_seconds)

            except Exception as exc:
                if is_overquota_error(exc):
                    processed_changed = True
                    raise RuntimeError('Gmail ha bloccato temporaneamente IMAP per OVERQUOTA. Ho fermato lo scarico: attendi 30-60 minuti e poi riparti con massimo 5/10 mail.') from exc
                results.append({'uid': uid_s, 'stato': 'errore_su_messaggio', 'errore': str(exc)})
                if sleep_seconds:
                    time.sleep(sleep_seconds)

        if delete_after_save:
            imap.expunge()
        return results

    except imaplib.IMAP4.error as exc:
        if is_overquota_error(exc):
            raise RuntimeError('Gmail segnala OVERQUOTA: troppi comandi o troppa banda IMAP. Attendi 30-60 minuti, poi usa la Modalita sicura con 5/10 mail.') from exc
        raise
    finally:
        if processed_changed:
            save_processed_uids(processed, username, mailbox)
        try:
            imap.logout()
        except Exception:
            pass

