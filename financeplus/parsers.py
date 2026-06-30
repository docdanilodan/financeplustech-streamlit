import re
from pypdf import PdfReader


def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ''
    for page in reader.pages:
        text += (page.extract_text() or '') + '\n'
    return text


def clean_value(value):
    value = (value or '').replace('\r', ' ').replace('\n', ' ')
    value = re.sub(r'\s+', ' ', value).strip(' :-\t')
    return value[:180]


def find_value(pattern, text, default=''):
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return clean_value(match.group(1)) if match else default


def looks_like_person(line):
    line = clean_value(line)
    upper = line.upper()
    if len(line) < 6:
        return False
    blocked = ['AMMINISTRATORE', 'RAPPRESENTANTE', 'CARICA', 'REA', 'SEDE', 'IMPRESA', 'REGISTRO', 'CAPITALE', 'PEC', 'CODICE', 'FISCALE']
    if any(x in upper for x in blocked):
        return False
    words = [w for w in re.split(r'\s+', line) if len(w) > 1]
    return len(words) >= 2 and sum(w[:1].isupper() or w.isupper() for w in words) >= 2


def find_person_after_keywords(text):
    lines = [clean_value(x) for x in text.splitlines() if clean_value(x)]
    keys = ['AMMINISTRATORE UNICO', 'AMMINISTRATORI', 'LEGALE RAPPRESENTANTE', 'RAPPRESENTANTE LEGALE', 'TITOLARE DI CARICHE']
    for i, line in enumerate(lines):
        up = line.upper()
        if any(k in up for k in keys):
            direct = re.sub(r'(?i)amministratore unico|amministratori|legale rappresentante|rappresentante legale|titolare di cariche|cariche o qualifiche|:', '', line).strip()
            if looks_like_person(direct):
                return clean_value(direct)
            for nxt in lines[i + 1:i + 8]:
                if looks_like_person(nxt):
                    return clean_value(nxt)
    return ''


def detect_tipo_documento(text):
    up = text.upper()
    if any(x in up for x in ['VISURA', 'CAMERA DI COMMERCIO', 'REGISTRO IMPRESE', 'REA ', 'CCIAA']):
        return 'Visura'
    return 'Report'


def parse_report_pdf(uploaded_file):
    text = extract_pdf_text(uploaded_file)
    tipo = detect_tipo_documento(text)

    denominazione = (
        find_value(r'Denominazione\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Impresa\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Ragione sociale\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'([A-Z0-9 &\'\.]+\s+(?:S\.R\.L\.|SRL|S\.P\.A\.|SPA|S\.N\.C\.|SNC|S\.A\.S\.|SAS))', text)
    )

    piva = (
        find_value(r'Partita\s+IVA\s*[:\-]?\s*([0-9]{11})', text) or
        find_value(r'P\.?\s*IVA\s*[:\-]?\s*([0-9]{11})', text) or
        find_value(r'Codice\s+fiscale(?:\s+e\s+numero\s+d\'iscrizione)?\s*[:\-]?\s*([0-9]{11})', text) or
        find_value(r'C\.F\.\s*[:\-]?\s*([0-9]{11})', text)
    )

    sede = (
        find_value(r'Sede\s+legale\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Indirizzo\s+sede\s+legale\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Sede\s*[:\-]?\s*([^\n\r]+)', text)
    )

    attivita = (
        find_value(r'Attivit[aà]\s+svolta\s+normalizzata\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Attivit[aà]\s+prevalente\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Attivit[aà]\s+esercitata\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Codice\s+ATECO\s*[:\-]?\s*([^\n\r]+)', text)
    )

    amministratore = (
        find_value(r'Amministratore\s+unico\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Legale\s+rappresentante\s*[:\-]?\s*([^\n\r]+)', text) or
        find_value(r'Rappresentante\s+legale\s*[:\-]?\s*([^\n\r]+)', text) or
        find_person_after_keywords(text)
    )

    data = {
        'tipo_documento': tipo,
        'denominazione': denominazione,
        'piva': piva,
        'sede': sede,
        'attivita': attivita,
        'pec': find_value(r'PEC\s*[:\-]?\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})', text),
        'amministratore': amministratore,
        'affidabilita': find_value(r'Affidabilit[aà]\s+([A-Za-z]+)', text),
        'fido': find_value(r'Valore\s+Fido\s+Medio\s+Accordabile\s*(?:EUR|Euro)?\s*([0-9\.\,]+)', text),
        'ricavi': find_value(r'(?:FATTURATO|RICAVI)\s+([0-9\.\,]+)\s*(?:EUR|Euro)?', text),
        'mol': find_value(r'MOL\s+([0-9\.\,]+)\s*(?:EUR|Euro)?', text),
        'utile': find_value(r'UTILE/PERDITA\s+([0-9\.\,]+)\s*(?:EUR|Euro)?', text),
        'cash_flow': find_value(r'CASH\s+FLOW\s+([0-9\.\,]+)\s*(?:EUR|Euro)?', text),
        'indice_indebitamento': find_value(r'INDICE\s+INDEBITAMENTO\s+([0-9\,\.]+)', text),
    }
    return data, text
