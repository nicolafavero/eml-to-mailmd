# REQ-003: Lista allegati vuota con sintassi YAML convenzionale

**Implements:** UR-002
**Status:** completed

## Descrizione

Quando non ci sono allegati, il YAML prodotto è `- ""` (stringa vuota in lista).
Usare `attachments: []` che è più convenzionale e semanticamente corretto.

## Checklist

- [x] Modificare `build_mail_md()` per produrre `attachments: []` se lista vuota
- [x] Aggiornare esempio in README se necessario — non necessario (esempio mostra allegati non vuoti)

## Note di completamento

- Data: 2026-03-18
