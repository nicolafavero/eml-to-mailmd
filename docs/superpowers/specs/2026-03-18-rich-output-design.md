# UR-004: Output arricchito con Rich — Design Spec

**UR:** [UR-004](../../user-requests/UR-004/input.md)
**Date:** 2026-03-18
**Status:** Approved

## Overview

Arricchire l'output CLI di `eml_to_mailmd.py` con colori, simboli e formattazione
avanzata usando la libreria [Rich](https://github.com/Textualize/rich) di Textualize.

## Approccio scelto

**Approccio C — Rich diretto con funzioni helper leggere.** Nessuna astrazione
complessa, tutto resta nel file singolo `eml_to_mailmd.py`. Tre funzioni helper
incapsulano la logica di presentazione.

## Modifiche

### 1. Dipendenze e CLI

- `pyproject.toml`: aggiungere `"rich"` a `dependencies`
- `argparse`: aggiungere flag `--no-color` (action `store_true`)
- `Console` creata in `main()` tramite helper `create_console(no_color)`
- Rich disabilita automaticamente colori quando output rediretto (pipe/file);
  `--no-color` forza la disabilitazione anche su TTY

### 2. Output per-file con progress bar

- `rich.progress.Progress` mostra avanzamento durante la conversione
- Per ogni file processato, riga sotto la progress bar:
  - Successo: `✓ nome_file.eml → mail_nome_file.md` (verde)
  - Errore: `✗ nome_file.eml: messaggio errore` (rosso)
- Caso "0 file trovati": messaggio semplice, nessuna progress bar

### 3. Sommario finale in tabella

- `rich.table.Table` con colonne: File, Stato, Output
  - Successo: `✓ OK` + nome file output
  - Errore: `✗ Errore` + messaggio errore
- Riga di totale sotto la tabella:
  - Tutto ok: `Completato: N/N convertiti` (verde bold)
  - Con errori: `Completato: X/N convertiti, Y errori` (giallo bold)

### 4. Funzioni helper

Tre funzioni nello stesso file `eml_to_mailmd.py`:

- `create_console(no_color: bool) -> Console` — crea istanza Console configurata
- `print_result(console: Console, result: Result) -> None` — stampa riga ✓/✗ per-file
- `print_summary(console: Console, results: List[Result]) -> None` — stampa Table + totale

La `Console` viene passata come argomento. Nessuno stato globale.

### 5. Struttura di `main()` dopo le modifiche

```python
def main(argv=None) -> int:
    # ... argparse (con --no-color) ...
    # ... folder validation ...
    # ... find eml files ...

    console = create_console(args.no_color)

    if not emls:
        console.print("[yellow]Nessun file .eml/.elm trovato[/]")
        return 1

    results: List[Result] = []

    with Progress(console=console, ...) as progress:
        task = progress.add_task("Conversione...", total=len(emls))
        for p in emls:
            res = process_file(p)
            results.append(res)
            print_result(console, res)
            progress.advance(task)

    print_summary(console, results)

    return 3 if any(not r.ok for r in results) else 0
```

## Import aggiuntivi

```python
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
```

## Graceful degradation

- Rich auto-detecta TTY: se stdout non è un terminale, disabilita colori/markup
- Flag `--no-color` forza `Console(no_color=True, highlight=False)`
- Output resta leggibile in entrambi i casi (i simboli ✓/✗ sono caratteri Unicode, visibili anche senza colori)

## Vincoli

- Il file resta single-file (`eml_to_mailmd.py`)
- Nessuna regressione sulla funzionalità di conversione
- I codici di ritorno restano invariati (0, 1, 2, 3)
- Aggiornare `README.md` per documentare `--no-color`
