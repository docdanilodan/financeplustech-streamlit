import email
import imaplib
import io
import json
import re
from datetime import date
from email import policy
from pathlib import Path

from financeplus.db import insert_cliente, insert_documento, insert_mail, list_clienti
from financeplus.parsers import parse_report_pdf
from financeplus.storage import archive_uploaded_file

CONFIG_PATH = Path('data/mail_config.json')
TEMP_DIR = Path('archive/_temporanea_da_classificare')
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


def clean(value):
    value = str(value or '').replace('\r', ' ').replace('\n', ' ')
    return re.sub(r'\s+', ' ', value).strip()


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


def import_mail_attachments(config, since_date=None, limit=50, delete_after_save=False):
    host = config.get('host', 'imap.gmail.com')
    port = int(config.get('port', 993))
    username = config.get('username', '')
    password = config.get('password', '')
    mailbox = config.get('mailbox', 'INBOX')

    if not username or not password:
        raise ValueError('Inserisci e salva prima email e password/app password.')

    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(username, password)
    imap.select(mailbox)

    criteria = 'ALL'
    if since_date:
        criteria = f'(SINCE "{imap_since(since_date)}")'

    status, data = imap.uid('search', None, criteria)
    if status != 'OK':
        imap.logout()
        return []

    uids = data[0].split()[-int(limit):]
    results = []

    for uid in uids:
        status, msg_data = imap.uid('fetch', uid, '(RFC822)')
        if status != 'OK' or not msg_data or not msg_data[0]:
            continue

        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw, policy=policy.default)
        subject = clean(msg.get('subject', ''))
        sender = clean(msg.get('from', ''))
        body = body_from_message(msg)
        mail_date = clean(msg.get('date', ''))

        attachment_names = []
        matched_cliente_id = 0
        created_cliente = False
        matched_name = company_from_text(subject + ' ' + body)
        matched_data = {}

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

        if delete_after_save:
            imap.uid('store', uid, '+FLAGS', r'(\Deleted)')

        results.append({
            'uid': uid.decode() if isinstance(uid, bytes) else str(uid),
            'mittente': sender,
            'oggetto': subject,
            'cliente_id': matched_cliente_id,
            'cliente_creato': created_cliente,
            'cliente': matched_name,
            'allegati_salvati': saved_count,
            'temporanei': temp_count,
            'eliminata_da_casella': bool(delete_after_save),
        })

    if delete_after_save:
        imap.expunge()
    imap.logout()
    return results
