from pathlib import Path
import streamlit as st
from financeplus.db import init_db, insert_cliente, insert_collaboratore, insert_documento, insert_richiesta, insert_mail, insert_valutazione, list_clienti, list_collaboratori, list_documenti, list_richieste, list_mail, list_valutazioni
from financeplus.parsers import parse_report_pdf
from financeplus.reports import genera_pdf_valutazione
from financeplus.scoring import calcola_score_da_indicatori, valutazione_base
from financeplus.storage import archive_uploaded_file, get_storage_provider

st.set_page_config(page_title='FinancePlusTech', page_icon='🏦', layout='wide')


def css():
    st.markdown('''<style>
    .block-container {padding-top: 1.5rem;}
    .hero {background: linear-gradient(90deg,#0F2A56,#183B73); padding: 28px; border-radius: 18px; color: white; margin-bottom: 22px; box-shadow: 0 12px 32px rgba(15,42,86,.18);} 
    .hero h1 {margin:0; font-size:34px;} .hero p {margin:8px 0 0 0; opacity:.9;}
    </style>''', unsafe_allow_html=True)


def hero():
    st.markdown('<div class="hero"><h1>🏦 FinancePlusTech Web App</h1><p>Archivio clienti, documenti, richieste, mail e valutazioni bancarie.</p></div>', unsafe_allow_html=True)


def clienti_options():
    c = list_clienti()
    if c.empty:
        return {}
    return {f"{r.denominazione or 'Senza nome'} | ID {r.id}": int(r.id) for r in c.itertuples()}


def dashboard():
    hero()
    a,b,c,d,e,f = st.columns(6)
    a.metric('Clienti', len(list_clienti()))
    b.metric('Collaboratori', len(list_collaboratori()))
    c.metric('Documenti', len(list_documenti()))
    d.metric('Richieste', len(list_richieste()))
    e.metric('Mail', len(list_mail()))
    f.metric('Valutazioni', len(list_valutazioni()))
    st.info(f'Archivio attivo: **{get_storage_provider()}**')
    st.subheader('Ultimi clienti')
    st.dataframe(list_clienti().head(20), use_container_width=True)


def nuovo_cliente():
    st.header('Nuovo Cliente')
    with st.form('cliente'):
        denominazione = st.text_input('Denominazione')
        piva = st.text_input('P.IVA / C.F.')
        sede = st.text_input('Sede')
        attivita = st.text_input('Attività')
        pec = st.text_input('PEC')
        amministratore = st.text_input('Amministratore')
        telefono = st.text_input('Telefono')
        email = st.text_input('Email')
        salva = st.form_submit_button('Salva cliente')
    if salva:
        i = insert_cliente(denominazione, piva, sede, attivita, pec, amministratore, telefono, email)
        st.success(f'Cliente salvato con ID {i}')


def elenco_clienti():
    st.header('Elenco Clienti')
    st.dataframe(list_clienti(), use_container_width=True)


def collaboratori():
    st.header('Collaboratori')
    with st.form('collaboratore'):
        nome = st.text_input('Nome')
        cognome = st.text_input('Cognome')
        cellulare = st.text_input('Cellulare')
        email = st.text_input('Mail')
        salva = st.form_submit_button('Salva collaboratore')
    if salva:
        insert_collaboratore(nome, cognome, cellulare, email)
        st.success('Collaboratore salvato.')
    st.dataframe(list_collaboratori(), use_container_width=True)


def inserisci_report():
    st.header('Inserisci Report PDF')
    uploaded = st.file_uploader('Carica report PDF', type=['pdf'])
    if not uploaded:
        st.caption('Carica un report PDF. Il sistema prova a estrarre anagrafica e indicatori.')
        return
    data, _ = parse_report_pdf(uploaded)
    with st.form('review_report'):
        c1, c2 = st.columns(2)
        with c1:
            denominazione = st.text_input('Denominazione', data.get('denominazione',''))
            piva = st.text_input('P.IVA / C.F.', data.get('piva',''))
            sede = st.text_input('Sede', data.get('sede',''))
            attivita = st.text_input('Attività', data.get('attivita',''))
            pec = st.text_input('PEC', data.get('pec',''))
            amministratore = st.text_input('Amministratore', data.get('amministratore',''))
        with c2:
            ricavi = st.text_input('Ricavi', data.get('ricavi',''))
            mol = st.text_input('MOL', data.get('mol',''))
            utile = st.text_input('Utile', data.get('utile',''))
            cash_flow = st.text_input('Cash Flow', data.get('cash_flow',''))
            indice = st.text_input('Indice indebitamento', data.get('indice_indebitamento',''))
            st.text_input('Fido indicato nel report', data.get('fido',''))
        salva = st.form_submit_button('Conferma e salva cliente + report + valutazione')
    if salva:
        cliente_id = insert_cliente(denominazione, piva, sede, attivita, pec, amministratore, '', '')
        uploaded.seek(0)
        local_path, provider, cloud_id = archive_uploaded_file(cliente_id, 'Report', uploaded)
        insert_documento(cliente_id, 'Report', uploaded.name, local_path, provider, cloud_id)
        score, rating, rischio, fido = calcola_score_da_indicatori(ricavi, mol, utile, cash_flow, indice)
        insert_valutazione(cliente_id, score, rating, fido, valutazione_base(score, rating, rischio, fido), ricavi, mol, utile, cash_flow, indice)
        st.success('Report importato, cliente salvato e valutazione creata.')


def gestione_documenti():
    st.header('Gestione Documenti')
    opts = clienti_options()
    if not opts:
        st.warning('Prima inserisci almeno un cliente.')
        return
    label = st.selectbox('Cliente', list(opts.keys()))
    cliente_id = opts[label]
    categoria = st.selectbox('Categoria documento', ['Bilancio','Centrale Rischi','Bozza Bilancio','Report','Visura','Altro'])
    uploaded = st.file_uploader('Carica documento', type=['pdf','xlsx','csv','docx','txt'])
    if st.button('Salva documento') and uploaded:
        docs = list_documenti(cliente_id)
        if categoria in ['Bilancio','Centrale Rischi','Bozza Bilancio','Report'] and not docs[docs['categoria'] == categoria].empty:
            st.error('Esiste già un documento per questa categoria e cliente.')
            return
        local_path, provider, cloud_id = archive_uploaded_file(cliente_id, categoria, uploaded)
        insert_documento(cliente_id, categoria, uploaded.name, local_path, provider, cloud_id)
        st.success('Documento archiviato correttamente.')
    st.subheader('Documenti del cliente')
    st.dataframe(list_documenti(cliente_id), use_container_width=True)


def gestione_richieste():
    st.header('Gestione Richieste Doc Pratiche')
    opts = clienti_options()
    if not opts:
        st.warning('Prima inserisci almeno un cliente.')
        return
    label = st.selectbox('Cliente', list(opts.keys()))
    cliente_id = opts[label]
    with st.form('richiesta'):
        data = st.date_input('Data')
        canale = st.selectbox('Mail / Cell', ['Mail','Cell'])
        oggetto = st.text_area('Oggetto richiesta', height=150)
        stato = st.text_area('Stato richiesta', height=150)
        semaforo = st.selectbox('Semaforo', ['Giallo','Verde'])
        salva = st.form_submit_button('Salva richiesta')
    if salva:
        insert_richiesta(cliente_id, str(data), canale, oggetto, stato, semaforo)
        st.success('Richiesta salvata.')
    st.dataframe(list_richieste(cliente_id), use_container_width=True)


def mail():
    st.header('Mail')
    opts = clienti_options()
    if not opts:
        st.warning('Prima inserisci almeno un cliente.')
        return
    label = st.selectbox('Cliente', list(opts.keys()))
    cliente_id = opts[label]
    with st.form('mail'):
        data_mail = st.date_input('Data mail')
        direzione = st.selectbox('Direzione', ['Entrata','Uscita'])
        stato = st.text_input('Stato')
        responsabile = st.text_input('Responsabile')
        md = st.text_input('Destinatario / Mittente')
        oggetto = st.text_input('Oggetto')
        testo = st.text_area('Testo / note', height=170)
        allegato = st.text_input('Allegato')
        salva = st.form_submit_button('Salva mail')
    if salva:
        insert_mail(cliente_id, str(data_mail), direzione, stato, responsabile, md, oggetto, testo, allegato)
        st.success('Mail salvata.')
    st.dataframe(list_mail(cliente_id), use_container_width=True)


def valutazione():
    st.header('Valutazione Bancaria')
    opts = clienti_options()
    if not opts:
        st.warning('Prima inserisci almeno un cliente.')
        return
    label = st.selectbox('Cliente', list(opts.keys()))
    cliente_id = opts[label]
    docs = list_documenti(cliente_id)
    st.subheader('Documenti disponibili')
    st.dataframe(docs, use_container_width=True)
    required = {'Bilancio','Centrale Rischi','Bozza Bilancio'}
    existing = set(docs['categoria'].tolist()) if not docs.empty else set()
    missing = required - existing
    st.warning('Mancano documenti: ' + ', '.join(sorted(missing))) if missing else st.success('Documenti minimi presenti.')
    st.subheader('Simulazione manuale')
    c1,c2,c3 = st.columns(3)
    ricavi = c1.text_input('Ricavi','0')
    mol = c2.text_input('MOL','0')
    utile = c3.text_input('Utile','0')
    cash_flow = c1.text_input('Cash Flow','0')
    indice = c2.text_input('Indice indebitamento','0')
    if st.button('Esegui analisi'):
        score, rating, rischio, fido = calcola_score_da_indicatori(ricavi, mol, utile, cash_flow, indice)
        insert_valutazione(cliente_id, score, rating, fido, valutazione_base(score, rating, rischio, fido), ricavi, mol, utile, cash_flow, indice)
        st.success('Analisi generata.')
    if st.button('Genera report PDF'):
        pdf_path = genera_pdf_valutazione(cliente_id)
        if pdf_path:
            with open(pdf_path, 'rb') as fh:
                st.download_button('Scarica PDF valutazione', fh, file_name=Path(pdf_path).name, mime='application/pdf')
        else:
            st.error('Nessuna valutazione disponibile per questo cliente.')
    st.subheader('Storico valutazioni')
    st.dataframe(list_valutazioni(cliente_id), use_container_width=True)


def main():
    css(); init_db()
    with st.sidebar:
        st.title('🏦 FinancePlusTech')
        page = st.radio('Menu', ['Dashboard','Nuovo Cliente','Elenco Clienti','Collaboratori','Inserisci Report','Gestione Documenti','Gestione Richieste','Mail','Valutazione'])
    pages = {'Dashboard': dashboard, 'Nuovo Cliente': nuovo_cliente, 'Elenco Clienti': elenco_clienti, 'Collaboratori': collaboratori, 'Inserisci Report': inserisci_report, 'Gestione Documenti': gestione_documenti, 'Gestione Richieste': gestione_richieste, 'Mail': mail, 'Valutazione': valutazione}
    pages[page]()


if __name__ == '__main__':
    main()
