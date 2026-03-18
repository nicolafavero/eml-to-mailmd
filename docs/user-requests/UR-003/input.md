# UR-003: Verifica conversione e trash del file EML sorgente

**Author:** Nicola
**Created:** 2026-03-18
**Priority:** Medium

## Context

Dopo la conversione di un file .eml in .md, attualmente non viene fatto alcun controllo sulla correttezza dell'output né viene gestito il file sorgente. L'utente vuole che venga verificata la correttezza della conversione e, solo se il controllo viene superato, il file .eml sorgente venga spostato nel cestino del sistema operativo (non eliminato definitivamente).

## Requirements

- [ ] Dopo la conversione, verificare la correttezza del file .md generato (es. frontmatter YAML valido, body non vuoto, campi obbligatori presenti)
- [ ] Se la verifica ha successo, spostare il file .eml sorgente nel cestino del SO (non eliminazione definitiva)
- [ ] Se la verifica fallisce, lasciare il file .eml intatto e segnalare l'errore
- [ ] Valutare l'uso di una libreria come `send2trash` per il cestino cross-platform

## Acceptance Criteria

- [ ] Il file .md generato viene validato automaticamente dopo la conversione
- [ ] I file .eml convertiti con successo vengono spostati nel cestino del SO
- [ ] I file .eml la cui conversione fallisce restano intatti
- [ ] L'utente viene informato dell'esito (successo/fallimento) per ogni file
- [ ] All existing functionality still works (no regressions)
