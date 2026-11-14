---
name: git-an-toan
description: "Safe Git rules across all repositories (AureLysn Vault, Portfolio, and Subsystems): pre-flight checks, .git/index.lock handling, worktree isolation, and forbidden commands. Use before running any Git command that mutates state (commit, branch, checkout, reset, stash, worktree) or when user mentions 'git', 'worktree', 'index.lock', or 'nhánh'."
---

# `git-an-toan` — Safe Git Rules Across All Repositories

## 1. Pre-Flight Inspection (Read Before Mutating)

Before running any Git command that modifies the working tree or history, run a single read-only check:

```bash
git status --short --branch
git worktree list
```

1. **Check for `.git/index.lock`:**
   - Never run two mutating Git commands in parallel (`git add`, `git commit`, `git checkout`).
   - If `.git/index.lock` exists, check whether another Git process or session is active before removing it (see `git-cuu-ho`).
2. **Verify current branch and working tree:**
   - On the main vault tree (`D:\AureLysn`), the checked-out branch must remain `main` so Obsidian and concurrent sessions always read the canonical state.
   - Never run `git checkout <branch>`, `git switch`, or `gh pr checkout` directly on `D:\AureLysn` (blocked by `chan_checkout_cay_chinh.py`).
3. **The vault repository has no remote (`git remote -v` is empty; open item `HT-043`).** Until one is connected, vault work is committed **directly on `main`** in `D:\AureLysn` (Aurel, 2026-11-13): no branch, no worktree, no PR. `nhanh-va-commit` §2–§4 still apply in full; `pr-va-merge` does not apply to the vault. Repositories that have a remote keep the branch → PR flow.

---

## 2. Commands Blocked by `PreToolUse` Hooks

| Forbidden Action | Hook | Required Alternative |
|---|---|---|
| `git mv` on `.md` notes | `chan_git_mv.py` | Rename inside Obsidian, or update all inbound wikilinks, add the old stem to `aliases:`, and run `vault_doctor.py` (`[[AGENTS]]` Invariant 10) |
| `sed -i` / `sed --in-place` | `chan_sed_i.py` | Use `Edit` for single files or `vaultlib.write_keep_eol()` in Python (`[[ai-tool-and-environment-quirks]]`) |
| Temp scripts in `$TEMP` / `/tmp` | `chan_nhap_temp.py` | Put reusable scripts in `01_Origine/04_Tools/VaultTool/` or run `python -c "..."` |
| `<gate> \| tail; echo $?` | `chan_exit_sau_ong.py` | Run the gate without piping, or use `set -o pipefail` / `${PIPESTATUS[0]}` |
| Branch switch on `D:\AureLysn` | `chan_checkout_cay_chinh.py` | Create an external worktree (`D:\AureLysn-wt\<slug>`); use `git checkout -- <file>` only for single-file restore |

---

## 3. Commands Requiring Explicit User Confirmation

Never execute any of the following without Aurel's explicit confirmation in the current turn:
- `git reset --hard`, `git checkout -- .`, `git restore .`, `git clean -fd`
- `git push --force` or `git push --force-with-lease`
- `git branch -D <branch>` on unmerged branches
- `rm` on any vault note or storage file (move to `_to_delete/<YYYY-MM-DD>/` instead — `[[AGENTS]]` Invariant 3)

---

## 4. Worktree Isolation (`git worktree`)

For a repository with a remote, or for the vault when Aurel asks for an isolated branch (the default for the vault is §1.3: commit on `main`). A vault branch made this way has no PR to come back through: it returns by `git -C D:/AureLysn merge --ff-only <type>/<slug>` after Aurel agrees, and is then removed as in step 3.

When working on an isolated feature branch while the main tree (`D:\AureLysn`) stays on `main`:
1. Place external worktrees **outside** the vault directory (`D:\AureLysn-wt\<branch-slug>`) so they do not bloat zip snapshots or nested file scans:
   ```bash
   git worktree add ../AureLysn-wt/<slug> -b <type>/<slug>
   ```
2. If the Claude Code desktop app creates a worktree inside `.claude/worktrees/<name>`, verify `.claude/worktrees/` is listed in `.gitignore` and `.vaultignore`.
3. After the branch is merged into `main` (by PR, `pr-va-merge`, or for the vault by the fast-forward merge above), remove the worktree and delete the merged branch.

---

## 5. Line Endings (`LF` vs `CRLF`)

The vault `.gitattributes` declares `text eol=lf` for `*.md`, `*.py`, `*.yaml`, `*.yml`, `*.json` and `*.txt` (`[[09-gates]]` §4): Git stores these with `LF` and converts a `CRLF` copy when it is staged. `*.db`, `*.epub`, `*.zip`, `*.bin` and `*.bak-*` are `binary`; `*.orig` is `-text` (bytes kept as they are). Other repositories may have no such file (`[[ai-tool-and-environment-quirks]]`):
- Always check `git diff --stat` before committing.
- In the vault, a tool that wrote `CRLF` into one of the six text types shows as the warning `CRLF will be replaced by LF`, not as a large diff. The file on disk is still wrong: write it back with `LF` via `vaultlib.write_keep_eol()`.
- In a repository without that declaration, or for a file type it does not list, a 5-line edit that shows a 200-line diff means the tool flipped line endings (`LF` ↔ `CRLF`). Restore and re-apply preserving the original line endings (`git-cuu-ho` Case 2).
