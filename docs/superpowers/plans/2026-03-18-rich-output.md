# UR-004: Rich CLI Output — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich CLI output of `eml_to_mailmd.py` with colors, symbols, progress bar, and summary table using the Rich library.

**Architecture:** Three lightweight helper functions (`create_console`, `print_result`, `print_summary`) added to the existing single file. `main()` refactored to accumulate results, conditionally show a progress bar (>5 files), and display a summary table. Pre-Console errors (exit code 2) remain plain `print()` to stderr.

**Tech Stack:** Python 3.11+, Rich (Textualize), hatchling build

**Spec:** `docs/superpowers/specs/2026-03-18-rich-output-design.md`

---

### Task 1: Add Rich dependency and install

**Files:**
- Modify: `pyproject.toml:7` (dependencies line)

- [ ] **Step 1: Add `rich` to dependencies**

In `pyproject.toml`, change:
```toml
dependencies = []
```
to:
```toml
dependencies = ["rich>=13.0"]
```

- [ ] **Step 2: Install the dependency**

Run: `cd /Users/nicola/Documents/projects/__projects/mail_to_md && uv sync`
Expected: rich installed, `uv.lock` updated

- [ ] **Step 3: Verify import works**

Run: `uv run python -c "from rich.console import Console; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Add rich dependency for CLI output formatting (UR-004)"
```

---

### Task 2: Add `--no-color` flag and `create_console()` helper

**Files:**
- Modify: `eml_to_mailmd.py` (add imports, add helper, modify argparse)

- [ ] **Step 1: Add Rich imports**

After the existing imports (line 19), add:
```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
```

- [ ] **Step 2: Add `create_console()` helper**

After the `Result` dataclass (after line 246), add:
```python
def create_console(no_color: bool = False) -> Console:
    """Create a Rich Console with optional color suppression."""
    return Console(no_color=no_color, highlight=False)
```

- [ ] **Step 3: Add `--no-color` argument to argparse**

In `main()`, after the `--recursive` argument (after line 314), add:
```python
parser.add_argument(
    "--no-color",
    action="store_true",
    help="Disabilita colori e formattazione nell'output.",
)
```

- [ ] **Step 4: Verify `--help` shows new flag**

Run: `uv run python eml_to_mailmd.py --help`
Expected: output shows `--no-color` flag in help text

- [ ] **Step 5: Commit**

```bash
git add eml_to_mailmd.py
git commit -m "Add --no-color flag and create_console() helper (UR-004)"
```

---

### Task 3: Add `print_result()` helper

**Files:**
- Modify: `eml_to_mailmd.py` (add function after `create_console`)

- [ ] **Step 1: Add `print_result()` function**

After `create_console()`, add:
```python
def print_result(console: Console, result: Result) -> None:
    """Print a single conversion result with status icon."""
    if result.ok:
        console.print(f"[green]✓[/] {result.src.name} → {result.out.name}")
    else:
        console.print(f"[red]✗[/] {result.src.name}: {result.message}")
```

- [ ] **Step 2: Commit**

```bash
git add eml_to_mailmd.py
git commit -m "Add print_result() helper for per-file output (UR-004)"
```

---

### Task 4: Add `print_summary()` helper

**Files:**
- Modify: `eml_to_mailmd.py` (add function after `print_result`)

- [ ] **Step 1: Add `print_summary()` function**

After `print_result()`, add:
```python
def print_summary(console: Console, results: List[Result]) -> None:
    """Print a summary table of all conversion results."""
    table = Table(title="Riepilogo conversione")
    table.add_column("File", style="cyan")
    table.add_column("Stato")
    table.add_column("Output")

    for r in results:
        if r.ok:
            table.add_row(r.src.name, "[green]✓ OK[/]", r.out.name)
        else:
            table.add_row(r.src.name, "[red]✗ Errore[/]", r.message)

    console.print()
    console.print(table)

    ok_count = sum(1 for r in results if r.ok)
    fail_count = len(results) - ok_count
    total = len(results)

    if fail_count == 0:
        console.print(f"\n[green bold]Completato: {ok_count}/{total} convertiti[/]")
    else:
        console.print(
            f"\n[yellow bold]Completato: {ok_count}/{total} convertiti, "
            f"{fail_count} errori[/]"
        )
```

- [ ] **Step 2: Commit**

```bash
git add eml_to_mailmd.py
git commit -m "Add print_summary() helper with Rich table (UR-004)"
```

---

### Task 5: Refactor `main()` to use Rich output

**Files:**
- Modify: `eml_to_mailmd.py:298-356` (the `main()` function)

- [ ] **Step 1: Replace the conversion loop and output in `main()`**

Replace everything in `main()` from `if not emls:` to the end (lines 335–356)
with the new Rich-based logic:

```python
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

Note: the pre-Console errors (exit code 2, folder validation) remain unchanged
as plain `print()` to `sys.stderr`.

- [ ] **Step 2: Verify `--help` still works**

Run: `uv run python eml_to_mailmd.py --help`
Expected: shows all flags including `--no-color` and `--recursive`

- [ ] **Step 3: Verify exit code 2 (bad folder)**

Run: `uv run python eml_to_mailmd.py /nonexistent; echo "Exit: $?"`
Expected: `ERRORE: cartella non trovata: /nonexistent` on stderr, exit code 2

- [ ] **Step 4: Verify exit code 1 (no .eml files)**

Run: `uv run python eml_to_mailmd.py /tmp; echo "Exit: $?"`
Expected: yellow "Nessun file .eml/.elm trovato", exit code 1

- [ ] **Step 5: Verify conversion with sample file**

Create a minimal test .eml and convert:
```bash
mkdir -p /tmp/test_rich_output
cat > /tmp/test_rich_output/test1.eml << 'EMAILEOF'
From: sender@example.com
To: recipient@example.com
Subject: Test email
Date: Mon, 17 Mar 2026 10:00:00 +0100
Content-Type: text/plain; charset="utf-8"

This is a test email body.
EMAILEOF

uv run python eml_to_mailmd.py /tmp/test_rich_output
echo "Exit: $?"
cat /tmp/test_rich_output/mail_test1.md
```
Expected: green `✓ test1.eml → mail_test1.md`, summary table with 1 row, exit code 0

- [ ] **Step 6: Verify `--no-color` flag**

Run: `uv run python eml_to_mailmd.py --no-color /tmp/test_rich_output`
Expected: same output but without ANSI color codes (plain text with ✓ symbol)

- [ ] **Step 7: Verify pipe output (graceful degradation)**

Run: `uv run python eml_to_mailmd.py /tmp/test_rich_output | cat`
Expected: plain text output, no ANSI escape sequences (Rich auto-detects non-TTY)

- [ ] **Step 8: Verify progress bar with >5 files**

```bash
mkdir -p /tmp/test_rich_progress
for i in $(seq 1 7); do
cat > /tmp/test_rich_progress/test${i}.eml << 'EMAILEOF'
From: sender@example.com
To: recipient@example.com
Subject: Test email
Date: Mon, 17 Mar 2026 10:00:00 +0100
Content-Type: text/plain; charset="utf-8"

Body of test email.
EMAILEOF
done

uv run python eml_to_mailmd.py /tmp/test_rich_progress
echo "Exit: $?"
```
Expected: progress bar visible (spinner + bar + percentage), 7 green ✓, summary table with 7 rows, exit code 0

- [ ] **Step 9: Cleanup test files**

```bash
rm -rf /tmp/test_rich_output /tmp/test_rich_progress
```

- [ ] **Step 10: Commit**

```bash
git add eml_to_mailmd.py
git commit -m "Refactor main() to use Rich output with progress bar and summary table (UR-004)"
```

---

### Task 6: Update documentation

**Files:**
- Modify: `README.md` (add `--no-color` documentation, update dependencies)
- Modify: `AGENTS.md:15` (update stdlib-only constraint)

- [ ] **Step 1: Update README.md**

Add `--no-color` to the usage/flags section. Update the "Requirements" section
to mention `rich` as a dependency. Update "Design Principles" to reflect
the dependency change.

- [ ] **Step 2: Update AGENTS.md**

On line 15, change:
```
  - Solo standard library (niente dipendenze esterne) salvo richiesta esplicita
```
to:
```
  - Dipendenze esterne minime: solo `rich` (output CLI). Nuove dipendenze richiedono richiesta esplicita
```

- [ ] **Step 3: Verify README renders correctly**

Read through the updated README to ensure formatting is correct.

- [ ] **Step 4: Commit**

```bash
git add README.md AGENTS.md
git commit -m "Update docs for Rich output and --no-color flag (UR-004)"
```
