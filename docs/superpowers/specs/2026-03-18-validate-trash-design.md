# UR-003: Verifica conversione e trash del file EML — Design Spec

**UR:** [UR-003](../../user-requests/UR-003/input.md)
**Date:** 2026-03-18
**Status:** Approved

## Overview

Dopo la conversione di un file `.eml` in `.md`, validare la correttezza del file
generato e, se la validazione passa, spostare il `.eml` sorgente nel cestino del
sistema operativo. Comportamento attivo di default, disattivabile con `--keep`.

## Approccio scelto

**Approccio B — Funzioni separate, orchestrazione in `main()`.** Due nuove funzioni
(`validate_mail_md`, `trash_source`) aggiunte allo stesso file. `process_file()`
modificata minimamente per esporre anche l'`EmailMessage` parsed. `main()` orchestra
la sequenza: converte → valida → cestina.

## Modifiche

### 1. Dipendenze e CLI

- `pyproject.toml`: aggiungere `"send2trash"` a `dependencies`
- `argparse`: aggiungere flag `--keep` (action `store_true`)
  - Default: trash attivo (converte → valida → cestina)
  - Con `--keep`: converte e basta (comportamento pre-UR-003)

```python
parser.add_argument(
    "--keep",
    action="store_true",
    help="Non cestinare i file .eml sorgente dopo la conversione.",
)
```

### 2. Funzione `validate_mail_md(md_path, msg)`

Validazione a 3 livelli del file `.md` generato:

**Struttura:**
- Il file esiste e non è vuoto
- Il frontmatter YAML è parsabile (delimitato da `---`)

**Contenuto:**
- Campi obbligatori presenti nel frontmatter: `from`, `date_raw`
- `subject` e `to` verificati solo per coerenza (possono essere legittimamente vuoti
  in email senza subject o con undisclosed recipients / BCC-only)
- Body (dopo il secondo `---`) non vuoto

**Coerenza (confronto normalizzato con EML sorgente):**

La strategia di confronto **non rilegge il YAML** ma rigenera i valori attesi con le
stesse funzioni usate in scrittura (`join_addrs()`, `yaml_escape()`) e li confronta
con le righe corrispondenti nel file `.md`. Questo evita la necessità di un parser YAML
e garantisce coerenza end-to-end.

Per ogni campo (`from`, `to`, `subject`):
1. Calcola il valore atteso: `yaml_escape(join_addrs(msg["From"]))` (o equivalente)
2. Cerca la riga corrispondente nel file .md (es. `from: "..."`)
3. Confronta dopo normalizzazione whitespace (collapse + strip)

Il confronto di coerenza viene eseguito solo quando il campo nell'EML sorgente è
non-vuoto. Se l'EML non ha `Subject`, il campo vuoto nel .md è accettato senza errore.

Firma: `validate_mail_md(md_path: Path, msg: EmailMessage) -> tuple[bool, list[str]]`
Ritorna `(ok, errors)` dove `errors` è la lista degli errori trovati (vuota se ok).

### 3. Funzione `trash_source(path)`

Wrapper leggero attorno a `send2trash`:

```python
def trash_source(path: Path) -> tuple[bool, str]:
    """Move source file to OS trash. Returns (success, message)."""
    try:
        send2trash(path)
        return True, "Cestinato"
    except Exception as e:
        return False, f"Errore cestino: {e}"
```

Se fallisce (permessi, filesystem senza cestino), il file resta intatto e l'errore
viene riportato. Non è un errore fatale — la conversione è comunque riuscita.

### 4. Estensione del `Result` dataclass

Nuovi campi con default per retrocompatibilità:

```python
@dataclass(frozen=True)
class Result:
    src: Path
    out: Path
    ok: bool
    message: str
    validated: bool = False
    trashed: bool = False
    trash_message: str = ""
    validation_errors: tuple[str, ...] = ()
```

`tuple` (immutabile) per `validation_errors` perché il dataclass è `frozen=True`.
I default garantiscono che `process_file()` continua a funzionare senza modifiche
alla sua return signature per il `Result`.

### 5. Modifica di `process_file()`

`process_file()` viene modificata per restituire anche l'`EmailMessage` parsed,
evitando di ri-parsare il .eml in `main()`.

Nuova firma: `process_file(path: Path) -> tuple[Result, Optional[EmailMessage]]`

La funzione ritorna `(result, msg)` dove `msg` è `None` in caso di errore di parsing.

**Nota:** entrambi i call site in `main()` (branch `use_progress` e branch `else`)
devono essere aggiornati per fare unpack della tupla.

### 6. Orchestrazione in `main()`

Il loop di conversione in entrambi i branch (progress e no-progress) viene aggiornato
per unpacking della tupla e accumulo di `msgs`:

```python
results: List[Result] = []
msgs: List[Optional[EmailMessage]] = []

# In entrambi i branch (use_progress e else):
for p in emls:
    res, msg = process_file(p)
    results.append(res)
    msgs.append(msg)
    print_result(console, res)
```

Dopo il loop di conversione, se `--keep` non è attivo, un secondo passaggio
sui risultati OK:

```python
# Validazione + trash (solo se non --keep)
if not args.keep:
    for i, res in enumerate(results):
        if not res.ok:
            continue
        valid, errors = validate_mail_md(res.out, msgs[i])
        if valid:
            trashed, trash_msg = trash_source(res.src)
            results[i] = Result(res.src, res.out, True, res.message,
                                validated=True, trashed=trashed)
        else:
            results[i] = Result(res.src, res.out, True, res.message,
                                validated=False, trashed=False,
                                validation_errors=tuple(errors))
        print_post_result(console, results[i])
```

Il `.md` generato resta sempre sul disco (anche se la validazione fallisce),
per consentire debug. Il `.eml` viene cestinato solo se la validazione passa.

La fase di validazione+trash non ha progress bar (è veloce: solo lettura file
e chiamata OS trash). Nessuna indicazione di progresso necessaria.

### 7. Output Rich aggiornato

**Per-file dopo validazione (`print_post_result`):**
- Validato e cestinato: `[green]  ↳ validato, cestinato[/]`
- Validato ma trash fallito: `[yellow]  ↳ validato, cestino fallito: ...[/]`
- Validazione fallita: `[yellow]  ↳ validazione fallita: ...[/]`

**Tabella sommario (`print_summary`):** nuova colonna "Post":
- `✓ cestinato` (verde) — validato e cestinato
- `⚠ non cestinato` (giallo) — validazione fallita o trash fallito
- vuoto — se `--keep` attivo o conversione fallita

**Riga totale estesa:**
- Tutto ok: `Completato: 5/5 convertiti, 5 cestinati`
- Con problemi: `Completato: 5/5 convertiti, 3 cestinati, 2 non cestinati`
- Con `--keep`: `Completato: 5/5 convertiti` (come prima, nessuna menzione trash)

## Import aggiuntivi

```python
from send2trash import send2trash
```

## Comportamento `--keep`

Con `--keep` attivo, il tool si comporta esattamente come prima della UR-003:
converte e basta, nessuna validazione, nessun trash. I campi `validated`, `trashed`,
`validation_errors` nel `Result` restano ai valori di default.

## Validazione fallita: cosa succede

- Il file `.md` resta sul disco (per debug)
- Il file `.eml` resta intatto (non cestinato)
- L'utente viene informato con i dettagli degli errori di validazione
- Il file conta come "convertito con successo" (exit code 0) ma "non cestinato"
- NON influenza l'exit code (la conversione in sé è riuscita)

## Exit codes

I codici di ritorno restano invariati:
- `0`: tutti i file convertiti con successo
- `1`: nessun file trovato
- `2`: cartella non trovata / non è una cartella
- `3`: uno o più file non convertiti (errore di parsing/scrittura)

La validazione fallita o il trash fallito NON cambiano l'exit code — la conversione
è comunque avvenuta. L'informazione è visibile nell'output Rich.

## Interazione con `--recursive`

`--recursive` e trash sono ortogonali. `send2trash` funziona con qualsiasi path
valido, inclusi file in sottocartelle. Nessun trattamento speciale necessario.

## File da aggiornare

- `eml_to_mailmd.py`: implementazione
- `pyproject.toml`: aggiungere `send2trash`
- `README.md`: documentare `--keep`, comportamento trash, validazione
- `AGENTS.md`: aggiornare dipendenze (`send2trash`)

## Vincoli

- Il file resta single-file (`eml_to_mailmd.py`)
- Nessuna regressione sulla funzionalità di conversione
- Con `--keep`, comportamento identico a pre-UR-003
- Pre-Console errors (exit code 2) restano plain `print()` a stderr
