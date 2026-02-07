## Stato / Decisione di adozione

Il repository ha adottato un sistema di task tracking a due livelli (UR → REQ) sotto `docs/`,
con struttura diversa rispetto alla bozza iniziale contenuta in questo prompt:

- **Struttura effettiva:** `docs/user-requests/`, `docs/working/`, `docs/archive/`
  (anziché `requests/pending/` e `requests/implemented/`)
- **UR-001 implementato** con adattamento strutturale: il concetto di base è stato mantenuto,
  ma la gerarchia di directory e il workflow sono stati ridefiniti.
- **Fonte di verità operativa:** [`docs/README.md`](../../README.md) descrive il workflow
  e le convenzioni attualmente in uso.

Il prompt originale è conservato integralmente di seguito a scopo di audit.

---

Prompt: Create Implementation Request Tracking System

  You are working in a Git repository for eml-to-mailmd, a single-file Python CLI tool (eml_to_mailmd.py) that converts .eml
  files to Markdown. The repo uses stdlib only, Python 3.11+, and pushes directly to main (no PR workflow).

  Create an implementation request tracking system with the following exact specifications.

  1. Directory Structure

  Create these directories and files:

  requests/
    pending/.gitkeep
    implemented/.gitkeep
    TEMPLATE.md
    README.md

  2. File: requests/TEMPLATE.md

  # REQ-NNN: Title goes here

  **Status:** Pending
  **Created:** YYYY-MM-DD
  **Priority:** Low | Medium | High
  **Estimated Effort:** Small (< 1h) | Medium (1-4h) | Large (4h+)

  ## Context

  Why this change is needed. Link to issues, discussions, or pain points.

  ## Requirements

  - [ ] Requirement one
  - [ ] Requirement two
  - [ ] Requirement three

  ## Technical Notes

  Implementation hints, constraints, or design considerations.
  Reference specific functions or areas of `eml_to_mailmd.py` if relevant.

  ## Acceptance Criteria

  - [ ] Criterion one
  - [ ] Criterion two
  - [ ] All existing functionality still works (no regressions)

  ## Implementation Notes

  _Fill in after completion._

  - **Commit:** `<hash>`
  - **Completed:** YYYY-MM-DD
  - **Notes:** Summary of what was done, any deviations from the original plan.

  3. File: requests/README.md

  # Implementation Requests

  Structured tracking for feature requests, bug fixes, and improvements.

  ## Directory Layout

  requests/
    pending/         ← open requests waiting for implementation
    implemented/     ← completed requests (moved here when done)
    TEMPLATE.md      ← template for new requests
    README.md        ← this file

  ## Naming Convention

  Format: `REQ-NNN_description-in-kebab-case.md`

  - `NNN` is a zero-padded 3-digit sequential number
  - Description is a short kebab-case summary
  - Examples:
    - `REQ-001_add-html-export.md`
    - `REQ-002_fix-emoji-subject.md`
    - `REQ-013_recursive-directory-support.md`

  To find the next number, check the highest existing number in both `pending/` and `implemented/`.

  ## Workflow

  ### Creating a new request

  1. Copy `TEMPLATE.md` to `pending/REQ-NNN_description.md`
  2. Replace `REQ-NNN` and `Title goes here` in the heading
  3. Fill in Status (`Pending`), Created date, Priority, and Estimated Effort
  4. Write the Context, Requirements, Technical Notes, and Acceptance Criteria sections
  5. Leave the Implementation Notes section empty
  6. Commit: `git add requests/pending/REQ-NNN_description.md && git commit -m "Add REQ-NNN: short description"`

  ### Working on a request

  1. Update the checklist items in Requirements and Acceptance Criteria as you progress
  2. Commit progress as normal with your implementation changes

  ### Completing a request

  1. Move the file from `pending/` to `implemented/`:
     git mv requests/pending/REQ-NNN_description.md requests/implemented/
  2. Update the file:
  - Change **Status** from `Pending` to `Implemented`
  - Check all completed items in Requirements and Acceptance Criteria
  - Fill in the **Implementation Notes** section (commit hash, date, notes)
  3. Commit: `git commit -m "Complete REQ-NNN: short description"`

  ### Tips

  - One request per file — keep them focused
  - Priority is informational, not enforced — use it to decide what to work on next
  - If a request is abandoned, delete the file and commit the removal
  - Requests can reference each other by number (e.g., "see REQ-005")

  4. Addition to AGENTS.md

  Append these lines at the end of the existing AGENTS.md file (do NOT replace existing content):


  ## Implementation Requests

  Feature requests and improvements are tracked in `requests/`.
  See [`requests/README.md`](./requests/README.md) for workflow and naming conventions.
  New requests go in `requests/pending/`, completed ones in `requests/implemented/`.

  5. Instructions

  - Create all directories and files exactly as specified above
  - Use .gitkeep files (empty) in pending/ and implemented/ so Git tracks the empty directories
  - Do NOT modify any existing source code files
  - Do NOT add any automation scripts — the system is entirely manual
  - Commit all changes in a single commit with message: Add implementation request tracking system
