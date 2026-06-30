# FinancePlusTech Streamlit Web App

Web app Streamlit per archivio clienti, collaboratori, documenti, richieste, mail e valutazioni bancarie.

## Funzioni incluse

- Dashboard con KPI
- Nuovo cliente
- Elenco clienti
- Collaboratori
- Inserimento report PDF
- Estrazione dati base da report PDF
- Gestione documenti
- Archivio locale, Google Drive o pCloud
- Gestione richieste documentali
- Mail
- Valutazione bancaria preliminare
- Generazione report PDF
- Dati demo

## Struttura progetto

```text
app.py
requirements.txt
README.md
AVVIA_WINDOWS.bat
.gitignore
financeplus/
  __init__.py
  db.py
  storage.py
  scoring.py
  reports.py
  parsers.py
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
