#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.message import Message
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, List, Optional
from typing import Any, cast
from zoneinfo import ZoneInfo

from rich.console import Console
from rich.markup import escape
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from send2trash import send2trash as _send2trash


ROME_TZ = ZoneInfo("Europe/Rome")


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self._chunks.append(data)

    def get_text(self) -> str:
        # Normalize whitespace a bit
        text = "".join(self._chunks)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def strip_html(raw_html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(raw_html)
    stripper.close()
    return html.unescape(stripper.get_text())


def yaml_escape(value: str) -> str:
    """Escape a string value for safe YAML double-quoted output."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _normalize_ws(s: str) -> str:
    """Collapse whitespace and strip for normalized comparison."""
    return " ".join(s.split())


def safe_filename(s: str) -> str:
    # Keep it predictable across OS/filesystems
    s = s.strip()
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s or "mail"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def join_addrs(header_value: str) -> str:
    # Return: 'Name <a@b>, Name2 <c@d>' or '' if none
    addrs = getaddresses([header_value]) if header_value else []
    pretty: List[str] = []
    for name, addr in addrs:
        if not addr:
            continue
        name = " ".join(name.split())
        if name:
            pretty.append(f'{name} <{addr}>')
        else:
            pretty.append(addr)
    return ", ".join(pretty)


def parse_date_raw_to_dt(date_raw: str) -> Optional[datetime]:
    if not date_raw:
        return None
    try:
        dt = parsedate_to_datetime(date_raw)
        # parsedate_to_datetime may return naive for weird inputs
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def pick_body(msg: EmailMessage) -> str:
    """
    Prefer text/plain (non-attachment). If absent, try text/html then strip tags.
    """
    # If not multipart, handle directly
    if not msg.is_multipart():
        ctype = msg.get_content_type()
        try:
            payload = msg.get_content()
        except Exception:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, (bytes, bytearray)):
                try:
                    payload = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
                except Exception:
                    payload = payload.decode("utf-8", errors="replace")
        if payload is None:
            return ""
        text = str(payload).strip()
        if ctype == "text/html":
            return strip_html(text)
        return text

    # Multipart: walk parts
    plain_candidates: List[str] = []
    html_candidates: List[str] = []

    for part in msg.walk():
        if part.is_multipart():
            continue

        disp = (part.get_content_disposition() or "").lower()
        if disp == "attachment":
            continue

        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue

        try:
            content = part.get_content()
        except Exception:
            raw = part.get_payload(decode=True)
            if raw is None:
                continue
            
            charset: str = part.get_content_charset() or "utf-8"

            if isinstance(raw, (bytes, bytearray)):
                try:
                    content = raw.decode(charset, errors="replace")
                except Exception:
                    content = raw.decode("utf-8", errors="replace")
            else:
                # Fallback: stubs a volte dicono che può essere altro
                content = str(raw)
        if content is None:
            continue
        content_str = str(content).strip()
        if not content_str:
            continue

        if ctype == "text/plain":
            plain_candidates.append(content_str)
        elif ctype == "text/html":
            html_candidates.append(content_str)

    if plain_candidates:
        return "\n\n".join(plain_candidates).strip()
    if html_candidates:
        return strip_html("\n\n".join(html_candidates)).strip()
    return ""


def list_attachment_names(msg: EmailMessage) -> List[str]:
    names: List[str] = []
    for part in msg.walk():
        if part.is_multipart():
            continue
        filename = part.get_filename()
        if filename:
            names.append(filename)
            continue
        disp = (part.get_content_disposition() or "").lower()
        if disp == "attachment":
            # Sometimes attachments have no filename
            names.append("(attachment senza nome)")
    return names


def load_eml(path: Path) -> EmailMessage:
    with path.open("rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)  # type: ignore[arg-type]
    return cast(EmailMessage, msg)


def build_mail_md(
    msg: Message,
    *,
    date_raw: str,
    date_iso: str,
    date_local: str,
    attachments: List[str],
    body: str,
) -> str:
    from_v = join_addrs(str(msg.get("From", "")))
    to_v = join_addrs(str(msg.get("To", "")))
    cc_v = join_addrs(str(msg.get("Cc", "")))
    bcc_v = join_addrs(str(msg.get("Bcc", "")))  # often absent in received mail
    subject_v = str(msg.get("Subject", "")).replace("\n", " ").strip()

    # YAML (simple, predictable)
    lines: List[str] = []
    lines.append("---")
    lines.append(f'from: "{yaml_escape(from_v)}"')
    lines.append(f'to: "{yaml_escape(to_v)}"')
    lines.append(f'cc: "{yaml_escape(cc_v)}"')
    lines.append(f'bcc: "{yaml_escape(bcc_v)}"')
    lines.append(f'subject: "{yaml_escape(subject_v)}"')
    lines.append(f'date_raw: "{yaml_escape(date_raw)}"')
    lines.append(f'date_iso: "{yaml_escape(date_iso)}"')
    lines.append(f'date_local: "{yaml_escape(date_local)}"')
    if attachments:
        lines.append("attachments:")
        for a in attachments:
            lines.append(f'  - "{yaml_escape(a)}"')
    else:
        lines.append("attachments: []")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    lines.append("")
    return "\n".join(lines)


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


def create_console(no_color: bool = False) -> Console:
    """Create a Rich Console with optional color suppression."""
    return Console(no_color=no_color, highlight=False)


def print_result(console: Console, result: Result) -> None:
    """Print a single conversion result with status icon."""
    if result.ok:
        console.print(f"[green]✓[/] {escape(result.src.name)} → {escape(result.out.name)}")
    else:
        console.print(f"[red]✗[/] {escape(result.src.name)}: {escape(result.message)}")


def print_summary(console: Console, results: List[Result]) -> None:
    """Print a summary table of all conversion results."""
    table = Table(title="Riepilogo conversione")
    table.add_column("File", style="cyan")
    table.add_column("Stato")
    table.add_column("Output")

    for r in results:
        if r.ok:
            table.add_row(escape(r.src.name), "[green]✓ OK[/]", escape(r.out.name))
        else:
            table.add_row(escape(r.src.name), "[red]✗ Errore[/]", escape(r.message))

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


def process_file(path: Path) -> tuple[Result, Optional[EmailMessage]]:
    try:
        msg = load_eml(path)
    except Exception as e:
        return Result(path, Path(), False, f"Errore parsing EML: {e}"), None

    date_raw = str(msg.get("Date", "")).strip()
    dt = parse_date_raw_to_dt(date_raw)

    if dt is None:
        # Keep empty but explicit
        date_iso = ""
        date_local = ""
    else:
        date_iso = dt.isoformat(timespec="seconds")
        date_local = dt.astimezone(ROME_TZ).isoformat(timespec="seconds")

    attachments = list_attachment_names(msg)
    body = pick_body(msg)

    base = safe_filename(path.stem)
    out = path.with_name(f"mail_{base}.md")
    out = unique_path(out)

    md = build_mail_md(
        msg,
        date_raw=date_raw,
        date_iso=date_iso,
        date_local=date_local,
        attachments=attachments,
        body=body,
    )

    try:
        out.write_text(md, encoding="utf-8")
    except Exception as e:
        return Result(path, out, False, f"Errore scrittura output: {e}"), msg

    return Result(path, out, True, "OK"), msg


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


def trash_source(path: Path) -> tuple[bool, str]:
    """Move source file to OS trash. Returns (success, message)."""
    try:
        _send2trash(path)
        return True, "Cestinato"
    except Exception as e:
        return False, f"Errore cestino: {e}"


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


def find_eml_files(folder: Path) -> List[Path]:
    # Support both .eml and .elm (typo-proof), case-insensitive
    files: List[Path] = []
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in (".eml", ".elm"):
            files.append(p)
    return sorted(files)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eml_to_mailmd",
        description="Converte file .eml/.elm in mail_*.md con header + date_raw/date_iso/date_local + allegati + corpo.",
    )
    parser.add_argument(
        "folder",
    nargs="?",
    default=".",
    type=str,
    help="Cartella da scandire (default: cartella corrente). Verranno cercati *.eml e *.elm.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scansiona ricorsivamente (default: no).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disabilita colori e formattazione nell'output.",
    )

    args = parser.parse_args(argv)

    folder = Path(args.folder).expanduser()

    if not folder.exists():
        print(f"ERRORE: cartella non trovata: {folder}", file=sys.stderr)
        return 2
    if not folder.is_dir():
        print(f"ERRORE: il path non è una cartella: {folder}", file=sys.stderr)
        return 2

    if args.recursive:
        emls = sorted(
            p for p in folder.rglob("*")
            if p.is_file() and p.suffix.lower() in (".eml", ".elm")
        )
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
                res, _msg = process_file(p)
                results.append(res)
                print_result(console, res)
                progress.advance(task)
    else:
        for p in emls:
            res, _msg = process_file(p)
            results.append(res)
            print_result(console, res)

    print_summary(console, results)

    return 3 if any(not r.ok for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
