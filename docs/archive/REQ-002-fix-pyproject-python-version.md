# REQ-002: Correggere requires-python in pyproject.toml

**Implements:** UR-002
**Status:** completed

## Descrizione

`pyproject.toml` dichiara `requires-python = ">=3.14"` che è errato.
Il progetto richiede Python 3.11+ come da AGENTS.md e README.

## Checklist

- [x] Cambiare `">=3.14"` in `">=3.11"` in pyproject.toml

## Note di completamento

- Data: 2026-03-18
