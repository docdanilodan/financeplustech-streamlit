from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from financeplus.db import get_cliente, list_valutazioni


def genera_pdf_valutazione(cliente_id):
    cliente = get_cliente(cliente_id)
    vals = list_valutazioni(cliente_id=cliente_id)
    if cliente is None or vals.empty:
        return None
    v = vals.iloc[0]
    out_dir = Path('pdf_valutazioni')
    out_dir.mkdir(exist_ok=True)
    filename = out_dir / f'valutazione_cliente_{cliente_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    doc = SimpleDocTemplate(str(filename), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph('FinancePlusTech - Report Valutazione Bancaria', styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Anagrafica cliente', styles['Heading2']))
    story.append(Paragraph(f"Denominazione: {cliente.get('denominazione','')}", styles['Normal']))
    story.append(Paragraph(f"P.IVA/C.F.: {cliente.get('piva','')}", styles['Normal']))
    story.append(Paragraph(f"Sede: {cliente.get('sede','')}", styles['Normal']))
    story.append(Paragraph(f"Attivita: {cliente.get('attivita','')}", styles['Normal']))
    story.append(Paragraph(f"PEC: {cliente.get('pec','')}", styles['Normal']))
    story.append(Spacer(1, 12))
    table_data = [
        ['Indicatore', 'Valore'],
        ['Score', str(v.get('score', ''))],
        ['Rating', str(v.get('rating', ''))],
        ['Fido stimato', f"EUR {float(v.get('fido_stimato', 0)):,.2f}"],
        ['Ricavi', str(v.get('ricavi', ''))],
        ['MOL', str(v.get('mol', ''))],
        ['Utile', str(v.get('utile', ''))],
        ['Cash Flow', str(v.get('cash_flow', ''))],
        ['Indice indebitamento', str(v.get('indice_indebitamento', ''))],
    ]
    table = Table(table_data, colWidths=[6 * cm, 10 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2A56')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))
    story.append(Paragraph('Giudizio', styles['Heading2']))
    story.append(Paragraph(str(v.get('giudizio', '')), styles['Normal']))
    doc.build(story)
    return filename
