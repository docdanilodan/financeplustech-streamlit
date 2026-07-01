# Mittenti autorizzati per lo scarico mail

La web app FinancePlusTech scarica **solo** le mail e gli allegati provenienti dai seguenti indirizzi:

```text
elibetty731@gmail.com
Valentinaboratto82@gmail.com
stefano.faraone@eurofintechsrl.it
praticheBS@proton.me
sergio.pedolazzi@katudi.it
paolo.baldinelli@katudi.it
pratiche@katudi.it
niccolo.sovico@ener2crowd.com
```

## Regola applicata

- La ricerca IMAP viene eseguita separatamente per ogni mittente autorizzato.
- Gli UID trovati vengono uniti ed eliminati i duplicati.
- Prima di salvare mail e allegati viene eseguito un secondo controllo sul campo `From`.
- Qualunque mail proveniente da un mittente diverso viene ignorata.

## Dove si modifica l'elenco

L'elenco e nel file:

```text
financeplus/mail_importer.py
```

Variabile:

```python
ALLOWED_SENDERS
```
