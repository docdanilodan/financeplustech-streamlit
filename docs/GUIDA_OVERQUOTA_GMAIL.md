# Guida errore Gmail OVERQUOTA

## Errore visualizzato

```text
[OVERQUOTA] Account exceeded command or bandwidth limits
```

## Significato

La password Gmail funziona, ma Gmail ha bloccato temporaneamente IMAP per troppi comandi o troppa banda in poco tempo.

Succede soprattutto quando:

- si cercanoo troppe mail insieme;
- si scaricano molti allegati pesanti;
- si preme più volte il pulsante Scarica/Cerca;
- l'app rilegge sempre le stesse mail già elaborate.

## Correzioni inserite in questa versione

- Scarico massimo 20 mail per ciclo.
- Valore consigliato: 5 o 10 mail.
- Pausa automatica tra una mail e la successiva.
- Filtro solo sugli 8 mittenti autorizzati.
- Ricerca Gmail ottimizzata con X-GM-RAW quando disponibile.
- Memoria UID delle mail già elaborate in `data/processed_mail_uids.json`.
- Scarico predefinito solo delle nuove mail non ancora processate.
- Stop automatico se Gmail restituisce OVERQUOTA.

## Cosa fare quando compare OVERQUOTA

1. Non premere più Scarica.
2. Attendi almeno 30-60 minuti.
3. Riapri l'app.
4. Imposta:

```text
Numero massimo mail da leggere per blocco: 5
Scarica solo nuove mail non già elaborate: attivo
Solo mail con allegati: attivo
Pausa tra una mail e la successiva: 2 secondi
```

5. Premi Scarica una sola volta.

## Nota importante

Se hai mostrato la password per app in uno screenshot, rigenerala subito da Google e aggiorna i Secrets di Streamlit.
