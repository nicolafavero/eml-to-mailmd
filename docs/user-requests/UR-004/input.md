# UR-004: Output arricchito con libreria Rich

**Author:** Nicola
**Created:** 2026-03-18
**Priority:** Low

## Context

L'output attuale del comando è testuale e minimale. L'utente desidera migliorare l'esperienza d'uso introducendo simboli, colori e formattazione avanzata nell'output del CLI, utilizzando la libreria "rich" di Textualize.

## Requirements

- [ ] Introdurre la libreria `rich` come dipendenza del progetto
- [ ] Arricchire l'output del CLI con colori, simboli e formattazione (es. progress bar, tabelle, icone di stato)
- [ ] Mantenere la leggibilità dell'output anche su terminali senza supporto colori (graceful degradation)
- [ ] Aggiornare la gestione delle dipendenze del progetto (eventuale pyproject.toml)

## Acceptance Criteria

- [ ] L'output del CLI usa colori e simboli per indicare successo, warning, errore
- [ ] L'output è leggibile anche su terminali senza supporto colori
- [ ] La libreria `rich` è dichiarata come dipendenza del progetto
- [ ] All existing functionality still works (no regressions)
