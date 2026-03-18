# AGENTS.md

## Scope
- Questo repository contiene una CLI Python singola (`eml_to_mailmd.py`) che converte file email `.eml/.elm` in file Markdown `mail_*.md` con frontmatter YAML.
- File core:
  - `eml_to_mailmd.py`: parsing email, estrazione metadati/allegati/corpo, YAML escaping, scrittura output
  - `pyproject.toml`: metadata progetto, entry point `eml2md`, build config (hatchling)
  - `CONTEXT.md`: stato corrente del progetto (letto a inizio sessione, aggiornato a fine sessione)
  - `README.md`: usage e formato output
- Vincoli tecnici:
  - Python 3.11+
  - Runtime ufficiale: `uv` / `uvx`
  - Fallback accettato: `python3` locale solo se `uv/uvx` non disponibile
  - Entry point CLI: `uv run eml2md` oppure `python3 eml_to_mailmd.py`
  - Dipendenze esterne minime: `rich` (output CLI), `send2trash` (cestino OS). Nuove dipendenze richiedono richiesta esplicita
- Comportamento atteso:
  - supporto `.eml` e `.elm` (case-insensitive)
  - output nella stessa cartella del sorgente
  - gestione collisioni filename con `_1`, `_2`, ...
  - date `date_raw`, `date_iso`, `date_local` (`Europe/Rome`)
  - corpo: preferire `text/plain`, fallback `text/html` con stripping

## Do/Don't
- Do:
  - leggere `CONTEXT.md` all'inizio della sessione per acquisire lo stato del progetto
  - aggiornare `CONTEXT.md` a fine sessione (stato, modifiche recenti, problemi noti, prossimi passi)
  - consultare `git log --oneline -10` per dettagli sulle modifiche recenti
  - leggere `README.md` e `eml_to_mailmd.py` prima di modificare
  - mantenere compatibilità CLI (`folder` opzionale, `--recursive`)
  - fare modifiche piccole, mirate al task
  - aggiornare `README.md` quando cambia il comportamento utente
  - mantenere output prevedibile e facile da processare
- Don't:
  - non introdurre dipendenze extra senza richiesta
  - non fare refactor ampi non necessari
  - non creare file/configurazioni aggiuntive senza richiesta
  - non usare comandi Git distruttivi (es. `reset --hard`) senza richiesta esplicita
  - non ignorare modifiche inattese nel working tree
  - non creare `main.py` o altri file entry point (l'unico sorgente è `eml_to_mailmd.py`)

## Validation Checklist
1. Eseguire `python3 eml_to_mailmd.py --help`.
2. Se disponibili `.eml/.elm`, fare almeno una conversione di prova.
3. Verificare che il file `mail_*.md` prodotto contenga:
   - frontmatter YAML con campi chiave (`from`, `to`, `subject`, date, `attachments`)
   - valori YAML correttamente escaped (backslash, doppi apici)
   - corpo non vuoto quando presente nel sorgente
4. Verificare che collisioni filename vengano risolte correttamente (`_1`, `_2`, ...).
5. Verificare che file con estensione maiuscola/mista (`.EML`, `.Eml`) vengano riconosciuti.

## Definition of Done
- Il comportamento richiesto dal task è implementato senza regressioni evidenti.
- La CLI continua a funzionare con interfaccia invariata (salvo richieste esplicite).
- Le verifiche minime della sezione `Validation Checklist` sono state eseguite.
- La documentazione utente (`README.md`) è allineata alle modifiche.

## Escalation Rules
- Fermarsi e chiedere conferma prima di:
  - introdurre nuove dipendenze o cambiare stack
  - modificare il formato output in modo breaking
  - cambiare timezone o semantica dei campi data
  - eseguire azioni distruttive su file o Git
- Se compaiono modifiche inattese non fatte dall'agente:
  - interrompere il lavoro
  - segnalare il fatto
  - chiedere come procedere

## Contesto di sessione

[`CONTEXT.md`](./CONTEXT.md) è il passaggio di consegne tra sessioni e agenti diversi.

**Protocollo obbligatorio:**
1. **Inizio sessione** — leggere `CONTEXT.md` per acquisire lo stato del progetto.
2. **Durante la sessione** — per dettagli su modifiche passate, consultare:
   - `git log --oneline -N` per una panoramica dei commit recenti
   - `git log --stat <hash>` o `git show <hash>` per i dettagli di un singolo commit
   - `git diff <hash1>..<hash2>` per confrontare due stati
3. **Fine sessione** — aggiornare `CONTEXT.md` con:
   - data e nome agente in "Ultimo aggiornamento"
   - stato attuale (cosa funziona, cosa è cambiato)
   - modifiche recenti (ultimi 3-5 commit significativi, con hash)
   - problemi noti (se nuovi o risolti)
   - prossimi passi (se cambiati)

> **Non usare session log separati**: `git log` è la fonte autorevole per la
> storia. `CONTEXT.md` cattura solo lo *stato corrente* e il *contesto operativo*
> che git non può esprimere (decisioni in sospeso, problemi noti, priorità).

## AI Agent Scaffolding

Questo repository usa file puntatore per supportare diversi agent AI:
- `CLAUDE.md` → Claude Code CLI
- `AGENTS.md` → OpenAI Codex CLI (questo file)
- `GEMINI.md` → Google Gemini CLI
- `.cursorrules` → Cursor
- `.github/copilot-instructions.md` → GitHub Copilot

Tutti puntano a questo file (`AGENTS.md`) come fonte unica di linee guida.
Non duplicare contenuti: aggiornare solo `AGENTS.md`.

## Task Tracking

User requests and implementation tasks are tracked in `docs/`.
See [`docs/README.md`](./docs/README.md) for the full workflow.

- `docs/user-requests/UR-NNN/input.md` — high-level requests (Author field identifies human or AI origin)
- `docs/working/REQ-NNN-*.md` — active implementation tasks
- `docs/archive/REQ-NNN-*.md` — completed tasks
