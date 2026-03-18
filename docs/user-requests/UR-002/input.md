# UR-002: Correzioni qualità da audit codebase

**Author:** Claude Opus 4.6 <!-- AI agents: always fill in your model name -->
**Created:** 2026-03-18
**Priority:** Medium

## Context

Un'analisi approfondita della codebase ha evidenziato diversi problemi di qualità:
bug nel `pyproject.toml`, HTML entity non decodificati, output YAML non convenzionale
per lista allegati vuota, indentazione PEP 8 errata, e exit code non documentati.

## Requirements

- [x] REQ-001: Decodifica HTML entity in `strip_html()` con `html.unescape()`
- [x] REQ-002: Correggere `requires-python` in `pyproject.toml` da `>=3.14` a `>=3.11`
- [x] REQ-003: Usare lista YAML vuota `[]` anziché `- ""` quando non ci sono allegati
- [x] REQ-004: Correggere indentazione PEP 8 (3 spazi → 4) a riga 148
- [x] REQ-005: Documentare exit code (0, 1, 2, 3) nel README

## Acceptance Criteria

- [ ] `python3 eml_to_mailmd.py --help` funziona correttamente
- [ ] HTML entity (`&nbsp;`, `&amp;`, ecc.) vengono decodificati nel body
- [ ] Allegati vuoti producono `attachments: []` nel YAML
- [ ] Nessuna violazione PEP 8 nel codice modificato
- [ ] Exit code documentati nel README
- [ ] `pyproject.toml` riporta `requires-python = ">=3.11"`
- [ ] Nessuna regressione sulle funzionalità esistenti
