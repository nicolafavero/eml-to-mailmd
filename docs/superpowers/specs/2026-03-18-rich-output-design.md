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
- Progress bar mostrata solo se `len(emls) > 5`; per 1-5 file, solo righe ✓/✗
- La stampa dentro il contesto `Progress` è intenzionale: Rich gestisce
  il live-rendering evitando output garbled. In modalità `no_color` o pipe,
  la progress bar degrada a testo semplice

### 3. Sommario finale in tabella

- `rich.table.Table` con colonne: File, Stato, Output
  - Successo: `✓ OK` + nome file output
  - Errore: `✗ Errore` + messaggio errore
- Riga di totale sotto la tabella:
  - Tutto ok: `Completato: N/N convertiti` (verde bold)
  - Con errori: `Completato: X/N convertiti, Y errori` (giallo bold)
- La tabella è sempre mostrata (anche per un solo file), per consistenza

### 4. Funzioni helper

Tre funzioni nello stesso file `eml_to_mailmd.py`:

- `create_console(no_color: bool) -> Console` — crea istanza Console configurata.
  Parametri: `Console(highlight=False)` normalmente,
  `Console(no_color=True, highlight=False)` con `--no-color`.
  `highlight=False` sempre per evitare auto-colorazione di path e numeri.
- `print_result(console: Console, result: Result) -> None` — stampa riga ✓/✗ per-file
- `print_summary(console: Console, results: List[Result]) -> None` — stampa Table + totale

La `Console` viene passata come argomento. Nessuno stato globale.

### 5. Struttura di `main()` dopo le modifiche

La logica esistente di `--recursive` e `find_eml_files()` resta invariata.
Le funzioni `process_file()` e `Result` dataclass sono usate così come sono.

```python
def main(argv=None) -> int:
    # ... argparse (con --no-color e --recursive, invariato) ...

    folder = Path(args.folder).expanduser()

    # Pre-Console errors: restano plain print() a stderr
    # perché Console non è ancora stata creata
    if not folder.exists():
        print(f"ERRORE: cartella non trovata: {folder}", file=sys.stderr)
        return 2
    if not folder.is_dir():
        print(f"ERRORE: il path non è una cartella: {folder}", file=sys.stderr)
        return 2

    # --recursive logic (invariata)
    if args.recursive:
        emls = sorted(...)
    else:
        emls = find_eml_files(folder)

    console = create_console(args.no_color)

    if not emls:
        console.print("[yellow]Nessun file .eml/.elm trovato[/]")
        return 1

    results: List[Result] = []
    use_progress = len(emls) > 5

    if use_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Conversione...", total=len(emls))
            for p in emls:
                res = process_file(p)
                results.append(res)
                print_result(console, res)
                progress.advance(task)
    else:
        for p in emls:
            res = process_file(p)
            results.append(res)
            print_result(console, res)

    print_summary(console, results)

    return 3 if any(not r.ok for r in results) else 0
```

## Import aggiuntivi

```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
```

## Output streams

- **Exit code 2** (cartella non trovata / non è una cartella): `print()` a `stderr`.
  Console non è ancora creata a questo punto.
- **Exit code 1** (nessun file trovato): `console.print()` a `stdout`.
- **Exit code 0/3** (conversione): tutto via `console.print()` a `stdout`.
  Gli errori per-file sono mostrati inline (rosso) ma vanno a `stdout`,
  coerentemente con il fatto che il sommario finale include tutto.

## Graceful degradation

- Rich auto-detecta TTY: se stdout non è un terminale, disabilita colori/markup
- Flag `--no-color` forza `Console(no_color=True, highlight=False)`
- Output resta leggibile in entrambi i casi (i simboli ✓/✗ sono caratteri Unicode,
  visibili anche senza colori)
- Progress bar in pipe/no-color: degrada a testo semplice (nessuna animazione)

## Vincoli

- Il file resta single-file (`eml_to_mailmd.py`)
- Nessuna regressione sulla funzionalità di conversione
- I codici di ritorno restano invariati (0, 1, 2, 3)
- File da aggiornare: `README.md` (documentare `--no-color`),
  `AGENTS.md` (aggiornare vincolo dipendenze per riflettere `rich`)
