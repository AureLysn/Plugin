---
name: nhanh-va-commit
description: "Branch naming (repositories with a remote; the vault commits on main while it has none), explicit file staging, pre-commit gate execution, and atomic commits. Use when creating a branch, staging changes, or committing work ('commit', 'tạo nhánh', 'lưu vào git')."
---

# `nhanh-va-commit` — Branching, Pre-Commit Gates & Atomic Commits

## 1. Branch Naming Convention

**Vault (`D:\AureLysn`):** while the repository has no remote (`HT-043`), do not create a branch; commit on `main` (`git-an-toan` §1.3) and go to §2. The naming below is for repositories with a remote, and for a vault branch Aurel asks for.

When creating a branch (inside an external worktree for `D:\AureLysn`, or directly in standalone repos):
- Format: `<type>/<short-kebab-slug>`
  - `feat/<slug>` — new feature, project, or subsystem capability
  - `fix/<slug>` — bug fix, broken link repair, or gate fix
  - `docs/<slug>` — documentation, MOC, schema, or rule update
  - `chore/<slug>` — tooling, index rebuild, or storage maintenance

---

## 2. Pre-Commit Verification Gates (Mandatory in `D:\AureLysn`)

If the repository root contains `AGENTS.md` and `01_Origine/`, run the verification gates from the vault root **before** creating a commit (`[[09-gates]]`):

1. **Rebuild the vault index AFTER all note edits are complete:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
   ```
   *(Note: `chan_commit_index_cu.py` blocks `git commit` if any `.md` note was edited after `vault_index.py --build`.)*
2. **Run `vault_doctor.py` (Root 1, Root 2, and Templates if templates changed):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --templates
   ```
3. **Run `claim_check.py` when system/MOC/store/agent files changed:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Validation/claim_check.py --no-scan
   ```
- **Gate Red (`exit 2`):** STOP and fix all errors before committing.

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
