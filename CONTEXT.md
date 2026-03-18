# CONTEXT.md

Stato corrente del progetto. Aggiornato dall'agente a fine sessione.

> **Regola**: ogni agente DEVE leggere questo file a inizio sessione e aggiornarlo
> prima di chiudere. Per dettagli sulle modifiche passate consultare `git log`.

Ultimo aggiornamento: 2026-03-18 — Claude Opus 4.6

## Stato attuale

Il progetto è una CLI Python single-file (`eml_to_mailmd.py`) che converte
email `.eml/.elm` in file Markdown con frontmatter YAML. Funzionalità core
completa e stabile. Nessun bug noto.

- CLI funzionante: `uv run eml2md [folder] [--recursive]` oppure `python3 eml_to_mailmd.py`
- Entry point registrato in `pyproject.toml` (build: hatchling)
- Zero dipendenze esterne (stdlib only, Python 3.11+)
- Scaffolding AI multi-agente attivo (CLAUDE.md, AGENTS.md, GEMINI.md, .cursorrules, .github/copilot-instructions.md)
- Task tracking two-tier operativo (UR → REQ, vedi docs/README.md)

## Modifiche recenti

- `2005730` — Scaffolding: uv alignment, CONTEXT.md, AI agent support, .gitignore completo
- `5534847` — Fix quality audit UR-002: html.unescape, pyproject >=3.11, attachments: [], PEP 8, exit codes in README
- `4d78b95` — Fix README: repo URL, comandi, wrapper script

## Problemi noti

- Nessun test unitario automatizzato (solo test manuali e ad-hoc)
- Timezone hardcoded `Europe/Rome` (by design, non un bug)
- `.python-version` pinna 3.14 (preferenza locale, gitignored)

## Prossimi passi

- Valutare aggiunta di test suite minimale (pytest, stdlib only)
- Valutare flag `--verbose` per visibilità su fallback charset/codec
- Valutare supporto timezone configurabile (bassa priorità)
