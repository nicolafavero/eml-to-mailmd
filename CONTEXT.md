# CONTEXT.md

Stato corrente del progetto. Aggiornato dall'agente a fine sessione.

> **Regola**: ogni agente DEVE leggere questo file a inizio sessione e aggiornarlo
> prima di chiudere. Per dettagli sulle modifiche passate consultare `git log`.

Ultimo aggiornamento: 2026-03-18 — Claude Opus 4.6

## Stato attuale

Il progetto è una CLI Python single-file (`eml_to_mailmd.py`) che converte
email `.eml/.elm` in file Markdown con frontmatter YAML. Funzionalità core
completa e stabile. Nessun bug noto.

- CLI funzionante: `uv run eml2md [folder] [--recursive] [--no-color] [--keep]`
- Entry point registrato in `pyproject.toml` (build: hatchling)
- Dipendenze esterne: `rich>=13.0` (output CLI), `send2trash>=1.8` (cestino OS)
- Python 3.11+
- Output arricchito con Rich: colori, simboli ✓/✗, progress bar (>5 file), tabella sommario
- Validazione post-conversione: struttura, contenuto, coerenza con EML sorgente
- Trash automatico del file `.eml` dopo validazione riuscita (disattivabile con `--keep`)
- Flag `--no-color`: disabilita colori/formattazione (auto-detect TTY per pipe)
- Scaffolding AI multi-agente attivo (CLAUDE.md, AGENTS.md, GEMINI.md, .cursorrules, .github/copilot-instructions.md)
- Task tracking two-tier operativo (UR → REQ, vedi docs/README.md)

## Modifiche recenti

- `0425562` — Fix contatore not_trashed per includere caso trash-failed (UR-003)
- `252cf0f` — Update docs per validazione, trash, --keep (UR-003)
- `00a00ef` — Orchestrazione validazione+trash in main() con --keep (UR-003)
- `6988f00` — Fix Rich markup injection in nomi file con brackets (UR-004)
- `ef754f6` — Refactor main() per output Rich con progress bar e tabella (UR-004)

## Problemi noti

- Nessun test unitario automatizzato (solo test manuali e ad-hoc)
- Timezone hardcoded `Europe/Rome` (by design, non un bug)
- `.python-version` pinna 3.14 (preferenza locale, gitignored)

## Prossimi passi

- Valutare aggiunta di test suite minimale (pytest)
- Valutare flag `--verbose` per visibilità su fallback charset/codec
- Valutare supporto timezone configurabile (bassa priorità)
