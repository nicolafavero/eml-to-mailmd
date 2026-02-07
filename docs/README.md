# Task Tracking Workflow

Two-tier system for tracking user requests and implementation tasks.

## Directory Layout

```
docs/
  user-requests/       ← high-level requests from the user
    UR-001/
      input.md         ← request description
      assets/          ← optional: screenshots, sample files, etc.
    TEMPLATE.md        ← template for new user requests
  working/             ← active implementation tasks (REQ files)
    REQ-001-add-html-export.md
    REQ-002-fix-emoji-subject.md
  archive/             ← completed tasks (moved from working/)
  README.md            ← this file
```

## Naming Conventions

### User Requests (UR)
- Format: `UR-NNN/input.md` (folder per request)
- `NNN` is a zero-padded 3-digit sequential number
- One `input.md` per folder; optional `assets/` subfolder for attachments
- Examples: `UR-001/`, `UR-012/`

### Implementation Tasks (REQ)
- Format: `REQ-NNN-description-kebab-case.md` (single file)
- `NNN` is a zero-padded 3-digit sequential number (global across working + archive)
- Examples: `REQ-001-add-html-export.md`, `REQ-015-fix-yaml-escaping.md`

## Workflow

### 1. Create a User Request

1. Create a new folder in `user-requests/`: `UR-NNN/`
2. Copy `user-requests/TEMPLATE.md` into it as `input.md`
3. Fill in title, context, requirements, and acceptance criteria
4. Add any supporting files in an `assets/` subfolder if needed
5. Commit: `git add docs/user-requests/UR-NNN/ && git commit -m "Add UR-NNN: short description"`

### 2. Break down into tasks

The coding agent (or the user) reads the UR and creates one or more `REQ-NNN-*.md` files in `working/`.

Each REQ file should contain:
- Reference to the parent UR (e.g., "Implements UR-001")
- Specific task description
- Checklist of subtasks

### 3. Work on tasks

1. Pick a REQ from `working/`
2. Implement the changes in the codebase
3. Update the checklist in the REQ file as you progress

### 4. Complete a task

1. Move the file from `working/` to `archive/`:
   ```
   git mv docs/working/REQ-NNN-description.md docs/archive/
   ```
2. Add implementation notes at the bottom (commit hash, date, summary)
3. Commit: `git commit -m "Complete REQ-NNN: short description"`

### 5. Close a User Request

When all REQs for a UR are archived, the UR is considered complete. Optionally add a note in `input.md` with the completion date.

## Tips

- One concern per UR — keep requests focused
- A single UR can generate multiple REQs
- REQs can reference each other (e.g., "see REQ-005")
- Priority in URs is informational, not enforced
- If a task is abandoned, delete the REQ file and commit the removal
