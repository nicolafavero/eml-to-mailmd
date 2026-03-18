# UR-003: Validate Conversion & Trash EML — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After converting .eml to .md, validate the output and move the source .eml to OS trash if validation passes. Active by default, disabled with `--keep`.

**Architecture:** Two new functions (`validate_mail_md`, `trash_source`) plus a `print_post_result` helper added to `eml_to_mailmd.py`. `process_file()` modified to also return the parsed `EmailMessage`. `main()` extended with a post-conversion validation+trash loop. `print_summary()` updated with a "Post" column. `Result` dataclass extended with `validated`, `trashed`, `validation_errors` fields.

**Tech Stack:** Python 3.11+, send2trash, Rich (already installed)

**Spec:** `docs/superpowers/specs/2026-03-18-validate-trash-design.md`

**Parallelism note:** Tasks 1+2 can run in parallel (different files). Tasks 3+4 can run in parallel (independent functions, same file but non-overlapping regions). Tasks 5-7 are sequential.

---

### Task 1: Add send2trash dependency

**Files:**
- Modify: `pyproject.toml:7` (dependencies line)

- [ ] **Step 1: Add `send2trash` to dependencies**

In `pyproject.toml`, change:
```toml
dependencies = ["rich>=13.0"]
```
to:
```toml
dependencies = ["rich>=13.0", "send2trash>=1.8"]
```

- [ ] **Step 2: Install the dependency**

Run: `cd /Users/nicola/Documents/projects/__projects/mail_to_md && uv sync`
Expected: send2trash installed, `uv.lock` updated

- [ ] **Step 3: Verify import works**

Run: `uv run python -c "from send2trash import send2trash; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Add send2trash dependency for OS trash support (UR-003)"
```

---

### Task 2: Extend Result dataclass and modify process_file() return type

**Files:**
- Modify: `eml_to_mailmd.py:245-333` (Result dataclass and process_file function)

- [ ] **Step 1: Add import for send2trash**

After line 24 (`from rich.table import Table`), add:
```python
from send2trash import send2trash as _send2trash
```

Note: aliased to `_send2trash` to avoid name collision with the function we'll create later called `trash_source`.

- [ ] **Step 2: Extend Result dataclass**

Replace the `Result` dataclass (lines 245-250) with:
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

- [ ] **Step 3: Modify process_file() to return tuple**

Change the function signature (line 295) from:
```python
def process_file(path: Path) -> Result:
```
to:
```python
def process_file(path: Path) -> tuple[Result, Optional[EmailMessage]]:
```

Change the error return (line 299) from:
```python
        return Result(path, Path(), False, f"Errore parsing EML: {e}")
```
to:
```python
        return Result(path, Path(), False, f"Errore parsing EML: {e}"), None
```

Change the write error return (line 331) from:
```python
        return Result(path, out, False, f"Errore scrittura output: {e}")
```
to:
```python
        return Result(path, out, False, f"Errore scrittura output: {e}"), msg
```

Change the success return (line 333) from:
```python
    return Result(path, out, True, "OK")
```
to:
```python
    return Result(path, out, True, "OK"), msg
```

- [ ] **Step 4: Update both call sites in main()**

In the progress branch (line 406), change:
```python
                res = process_file(p)
```
to:
```python
                res, _msg = process_file(p)
```

In the else branch (line 412), change:
```python
            res = process_file(p)
```
to:
```python
            res, _msg = process_file(p)
```

Note: using `_msg` for now since it's not consumed yet — Task 5 will wire it up.

- [ ] **Step 5: Verify nothing is broken**

Run: `uv run python eml_to_mailmd.py --help`
Expected: help output unchanged

Run:
```bash
mkdir -p /tmp/test_ur003
cat > /tmp/test_ur003/test1.eml << 'EMAILEOF'
From: sender@example.com
To: recipient@example.com
Subject: Test email
Date: Mon, 17 Mar 2026 10:00:00 +0100
Content-Type: text/plain; charset="utf-8"

This is a test email body.
EMAILEOF
uv run python eml_to_mailmd.py /tmp/test_ur003
echo "Exit: $?"
rm -rf /tmp/test_ur003
```
Expected: green ✓, summary table, exit 0 — identical to before

- [ ] **Step 6: Commit**

```bash
git add eml_to_mailmd.py
git commit -m "Extend Result dataclass and process_file() return type (UR-003)"
```

---

### Task 3: Add validate_mail_md() function

**Files:**
- Modify: `eml_to_mailmd.py` (add function after `process_file`)

- [ ] **Step 1: Add a normalize_ws() helper**

After `yaml_escape()` (after line 56), add:
```python
def _normalize_ws(s: str) -> str:
    """Collapse whitespace and strip for normalized comparison."""
    return " ".join(s.split())
```

- [ ] **Step 2: Add validate_mail_md() function**

After `process_file()`, add:
```python
def validate_mail_md(md_path: Path, msg: EmailMessage) -> tuple[bool, list[str]]:
    """Validate a generated .md file against its source EmailMessage.

    Three validation levels:
    - Structure: file exists, non-empty, has YAML frontmatter delimiters
    - Content: required fields present (from, date_raw), body non-empty
    - Coherence: field values match source EML (normalized comparison)

    Returns (ok, errors) where errors is empty if ok is True.
    """
    errors: list[str] = []

    # --- Structure ---
    if not md_path.exists():
        return False, ["File .md non trovato"]
    content = md_path.read_text(encoding="utf-8")
    if not content.strip():
        return False, ["File .md vuoto"]

    # Split on YAML delimiters
    parts = content.split("---")
    if len(parts) < 3:
        return False, ["Frontmatter YAML non trovato (delimitatori --- mancanti)"]

    frontmatter_text = parts[1]
    body = "---".join(parts[2:]).strip()

    # --- Content ---
    # Parse frontmatter lines into a dict
    fm: dict[str, str] = {}
    for line in frontmatter_text.strip().splitlines():
        if ":" in line and not line.startswith("  -"):
            key, _, value = line.partition(":")
            value = value.strip().strip('"')
            fm[key.strip()] = value

    # Required fields (must be present and non-empty)
    for field in ("from", "date_raw"):
        if not fm.get(field):
            errors.append(f"Campo obbligatorio mancante o vuoto: {field}")

    # Body must be non-empty
    if not body:
        errors.append("Body vuoto")

    # --- Coherence (only for non-empty source fields) ---
    coherence_checks = {
        "from": join_addrs(str(msg.get("From", ""))),
        "to": join_addrs(str(msg.get("To", ""))),
        "subject": str(msg.get("Subject", "")).replace("\n", " ").strip(),
    }
    for field, expected_raw in coherence_checks.items():
        if not expected_raw:
            continue  # Skip coherence check if source field is empty
        expected = _normalize_ws(yaml_escape(expected_raw))
        actual = _normalize_ws(fm.get(field, ""))
        if expected != actual:
            errors.append(
                f"Coerenza {field}: atteso \"{expected}\", trovato \"{actual}\""
            )

    return (len(errors) == 0, errors)
```

- [ ] **Step 3: Quick smoke test**

```bash
mkdir -p /tmp/test_validate
cat > /tmp/test_validate/test1.eml << 'EMAILEOF'
From: sender@example.com
To: recipient@example.com
Subject: Test email
Date: Mon, 17 Mar 2026 10:00:00 +0100
Content-Type: text/plain; charset="utf-8"

This is a test email body.
EMAILEOF
uv run python -c "
from pathlib import Path
from eml_to_mailmd import process_file, validate_mail_md
res, msg = process_file(Path('/tmp/test_validate/test1.eml'))
print('Conversion:', res.ok)
ok, errors = validate_mail_md(res.out, msg)
print('Validation:', ok, errors)
"
rm -rf /tmp/test_validate
```
Expected: `Conversion: True` then `Validation: True []`

- [ ] **Step 4: Commit**

```bash
git add eml_to_mailmd.py
git commit -m "Add validate_mail_md() with structure/content/coherence checks (UR-003)"
```

---

### Task 4: Add trash_source() and print_post_result() helpers

**Files:**
- Modify: `eml_to_mailmd.py` (add functions after `validate_mail_md`)

- [ ] **Step 1: Add trash_source() function**

After `validate_mail_md()` (or after `process_file()` if Task 3 hasn't been merged yet), add:
```python
def trash_source(path: Path) -> tuple[bool, str]:
    """Move source file to OS trash. Returns (success, message)."""
    try:
        _send2trash(path)
        return True, "Cestinato"
    except Exception as e:
        return False, f"Errore cestino: {e}"
```

- [ ] **Step 2: Add print_post_result() helper**

After `trash_source()`, add:
```python
def print_post_result(console: Console, result: Result) -> None:
    """Print post-conversion status (validation + trash)."""
    if result.validated and result.trashed:
        console.print(f"[green]  ↳ validato, cestinato[/]")
    elif result.validated and not result.trashed:
        err = escape(result.trash_message) if result.trash_message else "errore sconosciuto"
        console.print(f"[yellow]  ↳ validato, cestino fallito: {err}[/]")
    elif not result.validated and result.validation_errors:
        errors_str = escape("; ".join(result.validation_errors))
        console.print(f"[yellow]  ↳ validazione fallita: {errors_str}[/]")
```

- [ ] **Step 3: Commit**

```bash
git add eml_to_mailmd.py
git commit -m "Add trash_source() and print_post_result() helpers (UR-003)"
```

---

### Task 5: Add --keep flag and refactor main() orchestration

**Files:**
- Modify: `eml_to_mailmd.py:345-418` (main function)

- [ ] **Step 1: Add --keep argument to argparse**

After the `--no-color` argument block (after line 366), add:
```python
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Non cestinare i file .eml sorgente dopo la conversione.",
    )
```

- [ ] **Step 2: Add msgs accumulation in both branches**

In main(), after `results: List[Result] = []` (line 393), add:
```python
    msgs: List[Optional[EmailMessage]] = []
```

In the progress branch, change:
```python
                res, _msg = process_file(p)
                results.append(res)
```
to:
```python
                res, msg = process_file(p)
                results.append(res)
                msgs.append(msg)
```

In the else branch, change:
```python
            res, _msg = process_file(p)
            results.append(res)
```
to:
```python
            res, msg = process_file(p)
            results.append(res)
            msgs.append(msg)
```

- [ ] **Step 3: Add validation+trash loop after conversion**

Replace lines 416-418 (from `print_summary(console, results)` to `return 3 if ...`)
with the validation+trash logic followed by the summary and return:

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
                                    validated=True, trashed=trashed,
                                    trash_message=trash_msg)
            else:
                results[i] = Result(res.src, res.out, True, res.message,
                                    validated=False, trashed=False,
                                    validation_errors=tuple(errors))
            print_post_result(console, results[i])

    print_summary(console, results)

    return 3 if any(not r.ok for r in results) else 0
```

Note: `print_summary` is called AFTER the validation+trash loop so it shows
the final state including validation/trash status.

- [ ] **Step 4: Verify --help**

Run: `uv run python eml_to_mailmd.py --help`
Expected: shows `--keep`, `--no-color`, `--recursive`

- [ ] **Step 5: Verify --keep (backward compat)**

```bash
mkdir -p /tmp/test_keep
cat > /tmp/test_keep/test1.eml << 'EMAILEOF'
From: sender@example.com
To: recipient@example.com
Subject: Test
Date: Mon, 17 Mar 2026 10:00:00 +0100
Content-Type: text/plain; charset="utf-8"

Body.
EMAILEOF
uv run python eml_to_mailmd.py --keep /tmp/test_keep
echo "Exit: $?"
ls /tmp/test_keep/
```
Expected: exit 0, both `test1.eml` and `mail_test1.md` present (eml NOT trashed)

- [ ] **Step 6: Verify default behavior (validate + trash)**

```bash
cat > /tmp/test_keep/test2.eml << 'EMAILEOF'
From: sender@example.com
To: recipient@example.com
Subject: Test 2
Date: Mon, 17 Mar 2026 10:00:00 +0100
Content-Type: text/plain; charset="utf-8"

Body 2.
EMAILEOF
uv run python eml_to_mailmd.py /tmp/test_keep
echo "Exit: $?"
ls /tmp/test_keep/
```
Expected: exit 0, `test2.eml` is GONE (trashed), `mail_test2.md` present.
Output shows `↳ validato, cestinato`.

- [ ] **Step 7: Cleanup**

```bash
rm -rf /tmp/test_keep
```

- [ ] **Step 8: Commit**

```bash
git add eml_to_mailmd.py
git commit -m "Add --keep flag and validation+trash orchestration in main() (UR-003)"
```

---

### Task 6: Update print_summary() for new states

**Files:**
- Modify: `eml_to_mailmd.py` (print_summary function)

- [ ] **Step 1: Add "Post" column and update row logic**

Replace the entire `print_summary()` function with:
```python
def print_summary(console: Console, results: List[Result]) -> None:
    """Print a summary table of all conversion results."""
    has_post = any(r.validated or r.validation_errors for r in results)

    table = Table(title="Riepilogo conversione")
    table.add_column("File", style="cyan")
    table.add_column("Stato")
    table.add_column("Output")
    if has_post:
        table.add_column("Post")

    for r in results:
        if r.ok:
            stato = "[green]✓ OK[/]"
            output = escape(r.out.name)
        else:
            stato = "[red]✗ Errore[/]"
            output = escape(r.message)

        if has_post:
            if not r.ok:
                post = ""
            elif r.trashed:
                post = "[green]✓ cestinato[/]"
            elif r.validated and not r.trashed:
                post = "[yellow]⚠ cestino fallito[/]"
            elif r.validation_errors:
                post = "[yellow]⚠ non cestinato[/]"
            else:
                post = ""
            table.add_row(escape(r.src.name), stato, output, post)
        else:
            table.add_row(escape(r.src.name), stato, output)

    console.print()
    console.print(table)

    ok_count = sum(1 for r in results if r.ok)
    fail_count = len(results) - ok_count
    trashed_count = sum(1 for r in results if r.trashed)
    not_trashed = sum(1 for r in results if r.ok and r.validated is False and r.validation_errors)
    total = len(results)

    parts: list[str] = [f"{ok_count}/{total} convertiti"]
    if fail_count:
        parts.append(f"{fail_count} errori")
    if trashed_count:
        parts.append(f"{trashed_count} cestinati")
    if not_trashed:
        parts.append(f"{not_trashed} non cestinati")

    summary = ", ".join(parts)

    if fail_count or not_trashed:
        console.print(f"\n[yellow bold]Completato: {summary}[/]")
    else:
        console.print(f"\n[green bold]Completato: {summary}[/]")
```

- [ ] **Step 2: Verify with --keep (no Post column)**

```bash
mkdir -p /tmp/test_summary
cat > /tmp/test_summary/test1.eml << 'EMAILEOF'
From: sender@example.com
To: recipient@example.com
Subject: Test
Date: Mon, 17 Mar 2026 10:00:00 +0100
Content-Type: text/plain; charset="utf-8"

Body.
EMAILEOF
uv run python eml_to_mailmd.py --keep /tmp/test_summary
```
Expected: table with 3 columns (File, Stato, Output) — no "Post" column

- [ ] **Step 3: Verify without --keep (Post column visible)**

```bash
cat > /tmp/test_summary/test2.eml << 'EMAILEOF'
From: sender@example.com
To: recipient@example.com
Subject: Test 2
Date: Mon, 17 Mar 2026 10:00:00 +0100
Content-Type: text/plain; charset="utf-8"

Body 2.
EMAILEOF
uv run python eml_to_mailmd.py /tmp/test_summary
```
Expected: table with 4 columns, "Post" shows `✓ cestinato`, summary shows "cestinati"

- [ ] **Step 4: Cleanup and commit**

```bash
rm -rf /tmp/test_summary
git add eml_to_mailmd.py
git commit -m "Update print_summary() with Post column and trash stats (UR-003)"
```

---

### Task 7: Update documentation

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md:15`

- [ ] **Step 1: Update README.md**

Add documentation for:
- `--keep` flag in usage/flags section
- Default behavior: validate + trash after conversion
- Validation checks performed (structure, content, coherence)
- Update dependencies section to include `send2trash`

- [ ] **Step 2: Update AGENTS.md**

On the dependencies line, change:
```
  - Dipendenze esterne minime: solo `rich` (output CLI). Nuove dipendenze richiedono richiesta esplicita
```
to:
```
  - Dipendenze esterne minime: `rich` (output CLI), `send2trash` (cestino OS). Nuove dipendenze richiedono richiesta esplicita
```

- [ ] **Step 3: Verify README**

Read through updated README to ensure formatting is correct.

- [ ] **Step 4: Commit**

```bash
git add README.md AGENTS.md
git commit -m "Update docs for validation, trash, and --keep flag (UR-003)"
```
