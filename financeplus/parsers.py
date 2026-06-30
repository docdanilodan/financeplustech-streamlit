import re
from pypdf import PdfReader


def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ''
    for page in reader.pages:
        text += (page.extract_text() or '') + '\n'
    return text


def find_value(pattern, text, default=''):
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else default


def parse_report_pdf(uploaded_file):
    text = extract_pdf_text(uploaded_file)
    data = {
        'denominazione': find_value(r'Denominazione:\s*(.+)', text) or find_value(r'([A-Z0-9 &\.]+S\.R\.L\.)', text),
        'piva': find_value(r'(?:P\.?Iva|Partita IVA|C\.F\.|Cod\. fiscale:)\s*([0-9]{11})', text),
        'sede': find_value(r'Sede(?: legale)?:\s*(.+)', text),
        'attivita': find_value(r'Attivit[aà](?: svolta normalizzata)?:\s*(.+)', text),
        'pec': find_value(r'PEC:\s*([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})', text),
        'amministratore': find_value(r'Amministratore:\s*(.+)', text),
        'affidabilita': find_value(r'Affidabilit[aà]\s+([A-Za-z]+)', text),
        'fido': find_value(r'Valore Fido Medio Accordabile\s*(?:EUR|€)?\s*([0-9\.\,]+)', text),
        'ricavi': find_value(r'FATTURATO\s+([0-9\.\,]+)\s*(?:EUR|€)?', text),
        'mol': find_value(r'MOL\s+([0-9\.\,]+)\s*(?:EUR|€)?', text),
        'utile': find_value(r'UTILE/PERDITA\s+([0-9\.\,]+)\s*(?:EUR|€)?', text),
        'cash_flow': find_value(r'CASH FLOW\s+([0-9\.\,]+)\s*(?:EUR|€)?', text),
        'indice_indebitamento': find_value(r'INDICE INDEBITAMENTO\s+([0-9\,\.]+)', text),
    }
    return data, text
