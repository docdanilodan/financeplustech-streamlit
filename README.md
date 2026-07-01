# FinancePlusTech Streamlit Web App

Web app Streamlit per archivio clienti, collaboratori, documenti, richieste, mail, allegati e valutazioni bancarie.

## Funzioni incluse

- Dashboard con KPI
- Nuovo cliente
- Autocompilazione anagrafica da report PDF o visura camerale
- Estrazione automatica dati azienda, P.IVA, sede, attivita, PEC e amministratore
- Elenco clienti
- Collaboratori
- Inserimento report PDF o visura
- Scarico mail e allegati via IMAP
- Salvataggio configurazione mail: la inserisci una volta e poi riusi
- Creazione automatica cliente da allegati o testo mail
- Abbinamento automatico allegati al cliente
- Cartella temporanea per allegati non abbinati
- Download CSV di mail salvate
- Eliminazione mail selezionate dal gestionale
- Opzione eliminazione mail dalla casella dopo salvataggio
- Gestione documenti
- Archivio locale, Google Drive o pCloud
- Gestione richieste documentali
- Mail
- Valutazione bancaria preliminare
- Generazione report PDF
- Dati demo

## Come usare l'autocompilazione da report o visura

### Metodo 1: Nuovo Cliente

1. Vai su `Nuovo Cliente`.
2. Carica un report PDF o una visura camerale.
3. Il sistema compila automaticamente i campi disponibili.
4. Controlla e correggi.
5. Premi `Salva cliente`.

### Metodo 2: Inserisci Report/Visura

1. Vai su `Inserisci Report/Visura`.
2. Carica il PDF.
3. Il sistema riconosce se e un report o una visura.
4. Compila i dati azienda e amministratore.
5. Salva cliente e documento.
6. Se nel report ci sono indicatori economici, crea anche la valutazione.

## Come usare scarico mail e allegati

1. Vai su `Scarica Mail/Allegati`.
2. Inserisci host IMAP, porta, email, password/app password e cartella IMAP.
3. Premi `Salva configurazione mail`.
4. Dalla volta successiva non devi reinserire i dati.
5. Scegli data di partenza e numero massimo mail.
6. Premi `Scarica mail e allegati`.
7. Il sistema crea il cliente se lo riconosce.
8. Abbina gli allegati al cliente.
9. Gli allegati non riconosciuti finiscono in `archive/_temporanea_da_classificare`.

## Gestione mail salvate

Nella pagina `Mail` puoi:

- vedere tutte le mail salvate
- selezionare piu mail
- scaricarle in CSV
- eliminare le mail selezionate dal gestionale

## Struttura progetto

```text
app.py
requirements.txt
README.md
AVVIA_WINDOWS.bat
financeplus/
  __init__.py
  db.py
  storage.py
  scoring.py
  reports.py
  parsers.py
  mail_importer.py
.streamlit/
  config.toml
  secrets.example.toml
docs/
  GUIDA_INSTALLAZIONE.md
  GUIDA_UTILIZZO.md
sample_data/
  demo_state.json
archive/
  .gitkeep
data/
  .gitkeep
```

## Avvio locale su Windows

1. Scarica il repository come ZIP.
2. Estrai la cartella.
3. Fai doppio clic su `AVVIA_WINDOWS.bat`.

Oppure da prompt:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pubblicazione su Streamlit Cloud

1. Vai su Streamlit Cloud.
2. Crea una nuova app.
3. Seleziona questo repository GitHub.
4. Main file: `app.py`.
5. Inserisci eventuali secrets.
6. Premi Deploy.

## Archivio

La web app funziona subito con archivio locale. Per Google Drive o pCloud, copia `.streamlit/secrets.example.toml` nei secrets di Streamlit Cloud e configura provider, token e cartella.
