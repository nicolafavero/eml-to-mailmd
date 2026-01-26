#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def strip_html(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    stripper.close()
    return stripper.get_text()


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
    lines.append(f'from: "{from_v}"')
    lines.append(f'to: "{to_v}"')
    lines.append(f'cc: "{cc_v}"')
    lines.append(f'bcc: "{bcc_v}"')
    lines.append(f'subject: "{subject_v}"')
    lines.append(f'date_raw: "{date_raw}"')
    lines.append(f'date_iso: "{date_iso}"')
    lines.append(f'date_local: "{date_local}"')
    lines.append("attachments:")
    if attachments:
        for a in attachments:
            a_clean = a.replace('"', "'")
            lines.append(f'  - "{a_clean}"')
    else:
        lines.append('  - ""')
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


def process_file(path: Path) -> Result:
    try:
        msg = load_eml(path)
    except Exception as e:
        return Result(path, Path(), False, f"Errore parsing EML: {e}")

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
        return Result(path, out, False, f"Errore scrittura output: {e}")

    return Result(path, out, True, "OK")


def find_eml_files(folder: Path) -> List[Path]:
    # Support both .eml and .elm (typo-proof)
    files: List[Path] = []
    for ext in ("*.eml", "*.elm"):
        files.extend(folder.glob(ext))
    return sorted(set(files))


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

    args = parser.parse_args(argv)

    folder = Path(args.folder).expanduser()

    if not folder.exists():
        print(f"ERRORE: cartella non trovata: {folder}", file=sys.stderr)
        return 2
    if not folder.is_dir():
        print(f"ERRORE: il path non è una cartella: {folder}", file=sys.stderr)
        return 2

    if args.recursive:
        emls = sorted({p for p in folder.rglob("*.eml")} | {p for p in folder.rglob("*.elm")})
    else:
        emls = find_eml_files(folder)

    if not emls:
        print(f"NESSUN FILE: trovati 0 file .eml/.elm in: {folder}", file=sys.stderr)
        return 1

    ok = 0
    fail = 0

    for p in emls:
        res = process_file(p)
        if res.ok:
            ok += 1
            print(f"OK: {res.src.name} -> {res.out.name}")
        else:
            fail += 1
            print(f"ERRORE: {res.src.name}: {res.message}", file=sys.stderr)

    if fail:
        print(f"RISULTATO: OK={ok} ERRORI={fail}", file=sys.stderr)
        return 3

    print(f"RISULTATO: OK={ok} ERRORI=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
