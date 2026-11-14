---
name: git-cuu-ho
description: "Diagnose and recover from Git faults without losing work: stale index.lock, CRLF/LF full-file diffs, commits on the wrong branch, merge conflicts on vault-index.json, or recovering lost commits via reflog. Use when a Git command fails or git status shows unexpected state."
---

# `git-cuu-ho` — Git Fault Diagnosis & Safe Recovery

> **Golden Rule:** Never run `git reset --hard`, `git checkout -- .`, or `git clean -fd` to "fix" a Git error. Diagnose first with read-only commands so zero work is lost.

---

## Case 1 — `fatal: Unable to create '.../.git/index.lock': File exists`

1. Check if another `git` process is still running:
   ```bash
   ps aux | grep git
   ```
2. If no `git` process is running, the lock file is stale from a timed-out or interrupted command. Remove only the lock file:
   ```bash
   rm -f .git/index.lock
   ```
   *(For a worktree, check `<repo>/.git/worktrees/<name>/index.lock`.)*

---

## Case 2 — A Small Edit Produces a Full-File Diff (`LF` ↔ `CRLF` Flip)

**Where it happens:** a repository whose `.gitattributes` does not normalise the file's type. In the vault, `*.md`, `*.py`, `*.yaml`, `*.yml`, `*.json` and `*.txt` are `text eol=lf`, so a `CRLF` copy of one of them shows as the warning `CRLF will be replaced by LF` and not as a diff; for those, skip step 1 and write the file back with `V.LF` (`git-an-toan` §5).

**Symptom:** `git diff --stat` shows hundreds of lines changed on a file where only a few lines were edited (`[[ai-tool-and-environment-quirks]]`).
1. Confirm whether the diff is whitespace/line-ending noise:
   ```bash
   git diff -w <path>
   ```
2. Normalize the file back to the line-ending style recorded in `HEAD` using `vaultlib.write_keep_eol()`:
   ```bash
   python -c "from pathlib import Path; import sys; sys.path.insert(0, '01_Origine/04_Tools/VaultTool/Core'); import vaultlib as V; p = Path('<path>'); head_eol = V.CRLF if b'\r\n' in __import__('subprocess').check_output(['git', 'show', 'HEAD:<path>']) else V.LF; V.write_keep_eol(p, p.read_text(encoding='utf-8'), head_eol)"
   ```
3. Re-check `git diff --stat <path>` — only the intended lines should remain.

---

## Case 3 — Merge Conflict on Generated Index Files (`vault-index.json`)

**Symptom:** Merging `main` conflicts on `01_Origine/05_Meta/Index/vault-index.json` or `index.json`.
- **Never** resolve JSON index conflicts by hand. Accept either side, then rebuild deterministically from the merged notes:
  ```bash
  python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
  git add 01_Origine/05_Meta/Index/vault-index.json
  ```

---

## Case 4 — Committed on `main` Instead of a Feature Branch

This case is for a repository with a remote. In the vault, committing on `main` is the rule while it has no remote (`git-an-toan` §1.3); there is no `origin/main` to reset to.

If commits were made on local `main` before pushing:
1. Create a branch pointing at the current `HEAD` so the commits are preserved:
   ```bash
   git branch <type>/<slug> HEAD
   ```
2. Ask Aurel before resetting local `main` back to `origin/main`.

---

## Case 5 — Recovering a Lost Commit or Dropped Stash (`reflog`)

1. Inspect the reflog to locate the commit hash:
   ```bash
   git reflog -n 20
   ```
2. Inspect the commit contents read-only (`git show --stat <hash>`) and restore specific files via `git checkout <hash> -- <path>` or create a recovery branch (`git branch rescue/<slug> <hash>`).
