# Guida elementare installazione FinancePlusTech Web App

## 1. Cosa serve

- Python installato sul PC, se vuoi avviarla in locale.
- Account GitHub.
- Account Streamlit Cloud.
- Facoltativo: Google Drive o pCloud per archivio cloud.

## 2. Scaricare il progetto come ZIP da GitHub

1. Apri il repository `financeplustech-streamlit`.
2. Clicca sul pulsante verde `Code`.
3. Clicca `Download ZIP`.
4. Estrai lo ZIP sul desktop.

## 3. Avvio su Windows

1. Entra nella cartella estratta.
2. Fai doppio clic su `AVVIA_WINDOWS.bat`.
3. Attendi l'installazione delle dipendenze.
4. Si aprirà automaticamente il browser con la web app.

## 4. Avvio manuale

Apri il Prompt dei comandi nella cartella del progetto e scrivi:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 5. Pubblicazione online su Streamlit Cloud

1. Vai su Streamlit Cloud.
2. Clicca `New app`.
3. Seleziona il repository GitHub.
4. Come file principale inserisci `app.py`.
5. Premi `Deploy`.

## 6. Archivio locale

Se non configuri nulla, il sistema salva i file nella cartella `archive/` e il database nella cartella `data/`.

## 7. Archivio Google Drive

Nei secrets di Streamlit inserisci:

```toml
[storage]
provider = "google_drive"

[google_drive]
folder_id = "ID_CARTELLA_DRIVE"
```

Poi completa il blocco service account.

## 8. Archivio pCloud

Nei secrets di Streamlit inserisci:

```toml
[storage]
provider = "pcloud"

[pcloud]
access_token = "TOKEN_PCLOUD"
folder_id = "0"
```
