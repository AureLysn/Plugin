---
name: nhanh-va-commit
description: "Branch naming (every repository works by branch and PR), explicit file staging, running the repository's own gates before a commit, and atomic commits. Use when creating a branch, staging changes, or committing work ('commit', 'tạo nhánh', 'lưu vào git')."
---

# `nhanh-va-commit` — Branching, Pre-Commit Gates & Atomic Commits

## 1. Branch Naming Convention

**All repositories** (the vault root, `05_Evasion/`, `04_Portfolio/`, `Atelier`, `AureLysnOS`): no commit on `main`; every change is made on a branch and returns through a PR (`git-an-toan` §1.3, Aurel 2026-11-14).

When creating a branch (inside an external worktree for the three vault repositories, or directly in the app repositories):
- Format: `<type>/<short-kebab-slug>`
  - `feat/<slug>` — new feature, project, or subsystem capability
  - `fix/<slug>` — bug fix, broken link repair, or gate fix
  - `docs/<slug>` — documentation, MOC, schema, or rule update
  - `chore/<slug>` — tooling, index rebuild, or storage maintenance

---

## 2. Pre-Commit Verification Gates

Before creating a commit, run the repository's own verification gates and stop on a red gate (`exit 2`). This plugin does not define the gates; each repository does:

- **AureLysn Vault** (root holds `CLAUDE.md` and `01_Origine/`): the gate list, order and exit codes live in the `vault-ops` skill `kiem-tra-he-thong` (index rebuild last, then `vault_doctor`, then `claim_check`). The `vault-ops` hook `chan_commit_index_cu.py` blocks a commit whose staged notes are newer than the index.
- **`05_Evasion/` and `04_Portfolio/`**: the same `kiem-tra-he-thong` gates, run from `D:\AureLysn` after the merge is pulled (`git-an-toan` §4.1).
- **App repositories** (`Atelier`, `AureLysnOS`): the test or build command named in the repository's own `README` or `CLAUDE.md`. If none is named, say so in the commit report instead of inventing one.

---

## 3. Explicit Staging & Diff Inspection

1. **Never use `git add -A` or `git add .` blindly:**
   Stage only the specific files belonging to the current task:
   ```bash
   git add <file1> <file2> 01_Origine/05_Meta/Index/vault-index.json
   ```
   A step that changed many files (a vault-wide rename, an audit fix) stages the folders it worked in, by path, and leaves the rest of the tree alone:
   ```bash
   git add 01_Origine/03_Systems/Plugin 01_Origine/05_Meta/Index/vault-index.json
   ```
   Files another process keeps changing (the apps' `*.db`, `*.db-wal`, `*.db-shm`) are staged only when the step is about them.
2. **Inspect `git diff --cached --stat`:**
   - Confirm no untracked scratch files, `.env` secrets (`[[14-safety]]`), or `.test_claim_check_dang_chay` markers are staged.
   - Confirm line counts match the actual edit scope (catching accidental `LF`/`CRLF` flips).

---

## 4. Commit Message Format

Write concise Vietnamese or English commit messages stating **what changed and why**:

```bash
git commit -m "<type>(<scope>): <concise summary of what changed>"
```

After committing, run `git status --short` (`executed`) to confirm the staged changes were recorded cleanly.
