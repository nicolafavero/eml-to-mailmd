# mail-to-md

Convert `.eml` email files into structured Markdown files, optimized for project-based workflows.

The tool extracts email metadata, normalizes dates, lists attachments, and converts the email body into clean Markdown with YAML frontmatter.

---

## Features

- Parse `.eml` / `.elm` files (RFC 5322, case-insensitive extension matching)
- Generate one `mail_*.md` file per email
- YAML frontmatter with normalized metadata
- Three date representations:
  - `date_raw`: original email header (as-is)
  - `date_iso`: ISO 8601 with original timezone
  - `date_local`: ISO 8601 converted to Europe/Rome
- Attachment name listing
- Plain text body preferred, HTML stripped if needed
- Full body extraction with no line limit (all non-attachment text parts)
- Safe filename generation
- Automatic filename collision handling (`_1`, `_2`, …)

---

## Requirements

- Python 3.11+
- `uv` / `uvx`
- Standard library only (no external Python dependencies)

---

## Installation

Clone the repository:

```bash
git clone git@github.com:nicolafavero/eml-to-mailmd.git
```

Optional: create a wrapper command (example assumes `~/bin` is in PATH):

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT="$HOME/src/eml-to-mailmd/eml_to_mailmd.py"
python3 "$SCRIPT" "$@"
```

Save as `~/bin/eml2md` and make executable:

```bash
chmod +x ~/bin/eml2md
```

---

## Usage

### Convert emails in the current directory

```bash
eml2md
```

### Convert emails in a specific directory

```bash
eml2md /path/to/folder
```

### Direct script execution

```bash
python3 eml_to_mailmd.py /path/to/folder
```

---

## Input

- One or more `.eml` / `.elm` files (extension matching is case-insensitive)
- Default: non-recursive scan
- Optional `--recursive` flag supported

---

## Output

For each input email:

```
mail_<original-filename>.md
```

Generated in the same directory as the `.eml` file.

Filename collisions are handled automatically.

---

## Output Format (example)

```yaml
---
from: "Name <email@example.com>"
to: "Recipient <recipient@example.com>"
cc: ""
bcc: ""
subject: "Email subject"

date_raw: "Wed, 19 Nov 2025 10:13:29 +0000"
date_iso: "2025-11-19T10:13:29+00:00"
date_local: "2025-11-19T11:13:29+01:00"

attachments:
  - "layout.pdf"
  - "photo.jpg"
---
```

Followed by the email body in plain text.

---

## Design Principles

- Preserve original information (`date_raw`) for audit and traceability
- Provide canonical machine-friendly dates (`date_iso`)
- Provide human-friendly operational dates (`date_local`)
- Keep the format simple, predictable, and script-friendly
- Avoid external dependencies

---

## License

MIT
