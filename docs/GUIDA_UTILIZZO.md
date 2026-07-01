# Guida utilizzo FinancePlusTech Web App

## Dashboard

Mostra:

- clienti
- collaboratori
- documenti
- richieste
- mail
- valutazioni
- archivio attivo

## Nuovo Cliente con autocompilazione

Puoi inserire il cliente manualmente oppure caricare un report PDF o una visura camerale.

1. Vai su `Nuovo Cliente`.
2. Carica il PDF nel campo `Carica report PDF o visura per autocompilare`.
3. Il sistema prova a compilare automaticamente:
   - denominazione
   - P.IVA/C.F.
   - sede
   - attivita
   - PEC
   - amministratore / legale rappresentante
4. Controlla i dati.
5. Correggi eventuali errori.
6. Premi `Salva cliente`.

## Collaboratori

Inserisci:

- nome
- cognome
- cellulare
- mail

## Inserisci Report/Visura

1. Vai su `Inserisci Report/Visura`.
2. Carica un report PDF oppure una visura camerale.
3. Il sistema riconosce se il documento e un report o una visura.
4. Compila automaticamente i dati aziendali e l'amministratore.
5. Controlla e correggi i campi.
6. Conferma il salvataggio.
7. Il sistema salva cliente e documento.
8. Se trova ricavi, MOL, utile, cash flow o indebitamento, crea anche la valutazione.

## Scarica Mail/Allegati

Questa sezione serve per scaricare piu mail e piu allegati in automatico.

### Prima configurazione

1. Vai su `Scarica Mail/Allegati`.
2. Apri `Configurazione casella mail`.
3. Inserisci:
   - host IMAP
   - porta
   - email / username
   - password o app password
   - cartella IMAP, di solito INBOX
4. Premi `Salva configurazione mail`.

Dalla volta successiva non devi reinserire i dati: la configurazione resta salvata.

### Scarico automatico

1. Scegli la data di partenza.
2. Scegli quante mail leggere.
3. Premi `Scarica mail e allegati`.
4. Il sistema legge le mail.
5. Cerca il nome cliente nel testo, nell'oggetto e negli allegati PDF.
6. Se trova il cliente, abbina gli allegati.
7. Se il cliente non esiste, lo crea automaticamente.
8. Se non riesce ad abbinare, mette il file in `archive/_temporanea_da_classificare`.

### Eliminazione dalla casella mail

L'opzione `Elimina dalla casella mail dopo salvataggio riuscito` e disattivata di default.
Attivala solo se vuoi cancellare dalla casella le mail gia salvate nel gestionale.

## Gestione Documenti

Scegli cliente e categoria:

- Bilancio
- Centrale Rischi
- Bozza Bilancio
- Report
- Visura
- Altro

Il sistema blocca duplicati per le categorie principali.

## Gestione Richieste

Inserisci:

- data
- canale Mail/Cell
- oggetto richiesta
- stato richiesta
- semaforo giallo/verde

## Mail salvate

Nella pagina `Mail` puoi:

- vedere tutte le mail salvate
- inserire una mail manualmente
- selezionare piu mail
- scaricare le mail selezionate in CSV
- scaricare tutte le mail in CSV
- eliminare dal gestionale le mail selezionate

## Valutazione

1. Scegli cliente.
2. Verifica i documenti caricati.
3. Inserisci dati numerici per simulazione.
4. Premi `Esegui analisi`.
5. Premi `Genera report PDF`.
6. Scarica il PDF finale.
