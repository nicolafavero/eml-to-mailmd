# CONTEXT.md

Stato corrente del progetto. Aggiornato dall'agente a fine sessione.

> **Regola**: ogni agente DEVE leggere questo file a inizio sessione e aggiornarlo
> prima di chiudere. Per dettagli sulle modifiche passate consultare `git log`.

Ultimo aggiornamento: 2026-03-18 — Claude Opus 4.6 (sessione code review + fix)

## Stato attuale

Il progetto è una CLI Python single-file (`eml_to_mailmd.py`) che converte
email `.eml/.elm` in file Markdown con frontmatter YAML. Funzionalità core
completa e stabile. Ampia sessione di code review (3 reviewer: quality, tests,
security) con fix P1/P2/P3 applicati.

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

- `783ff03` — Merge fix/p1-fixes: 4 fix P1 (yaml_escape control chars, HTMLStripper script/style, nullcontext loop, regex frontmatter parser)
- `30053c7` — Clean up imports, type hints, costanti (P3 fixes)
- `1cdeb23` — Harden quality, security, resilience (P1+P2: yaml_escape newline, _decode_part, except specifici, MAX_EML_SIZE, validazione immediata, open(x))

## Code review

Report completo in `docs/code-review-report-v2.md` con 3 report individuali:
- `docs/review-quality.md` — Score: 7/10
- `docs/review-tests.md` — Coverage: 0%
- `docs/review-security.md` — Score: 7/10

## Problemi noti

- Nessun test unitario automatizzato (CRITICO — vedi review)
- Timezone hardcoded `Europe/Rome` (by design, non un bug)
- `.python-version` pinna 3.14 (preferenza locale, gitignored)
- `safe_filename()` senza troncamento (filename >255 byte possibile)
- Dipendenze non pinnate con upper bound

## Prossimi passi

- **P0**: Creare test suite pytest (9 casi P0 + 11 P1 identificati nella review)
- **P2**: Limite parti MIME, fallback except in process_file, pinnare dipendenze
- **P3**: Fix minori (costanti raggruppate, exit codes IntEnum, symlink handling)
