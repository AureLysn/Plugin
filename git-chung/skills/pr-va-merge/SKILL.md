---
name: pr-va-merge
description: "Push feature branches, open GitHub Pull Requests via gh CLI, verify CI checks, merge into main, and clean up worktrees, in a repository that has a remote (the vault has none yet). Use when user asks to 'tạo PR', 'merge nhánh', 'gộp vào main', 'push lên GitHub', or clean up after a PR."
---

# `pr-va-merge` — Pull Request Creation, Merge & Worktree Cleanup

## 0. Where This Skill Applies

- It needs a remote named `origin` and the `gh` CLI. Check first: `git remote -v`.
- **The vault repository (`D:\AureLysn`) has no remote** (open item `HT-043`). Until Aurel connects one, this skill does not apply there: vault work is committed on `main` (`git-an-toan` §1.3, `nhanh-va-commit`). If asked to "tạo PR" or "push" for the vault, say that there is no remote and stop; do not add one without Aurel's word.
- The `D:/AureLysn` lines in §3 describe the vault once it has a remote; for another repository, use its own main tree.

---

## 1. Preconditions Before Pushing

1. Confirm all commits on the branch passed the repository's verification gates (`nhanh-va-commit`).
2. Fetch the latest `origin/main` and check whether `main` has advanced:
   ```bash
   git fetch origin main
   git log HEAD..origin/main --oneline
   ```
3. If `origin/main` has new commits, rebase or merge `origin/main` into the feature branch inside the worktree, re-build `vault_index.py --build --include-fiction` if notes changed, and re-run `vault_doctor.py --include-fiction`.

---

## 2. Pushing & Opening the Pull Request (`gh pr create`)

1. Push the branch to `origin`:
   ```bash
   git push -u origin HEAD
   ```
2. Create the PR with a structured summary and verification section:
   ```bash
   gh pr create --base main --title "<concise title>" --body "## Tóm tắt thay đổi
   - ...

   ## Xác minh (Verify gate)
   - [x] vault_doctor --include-fiction (executed: 0 lỗi)
   - [x] vault_index --check (executed: khớp)"
   ```

---

## 3. Merging & Syncing the Main Tree (`D:\AureLysn`)

1. Inspect PR status and checks before merging:
   ```bash
   gh pr view --json state,mergeable,statusCheckRollup
   ```
2. Merge via `gh pr merge` (do **not** use `--admin` to bypass failing checks):
   ```bash
   gh pr merge <PR-number> --merge --delete-branch
   ```
3. Pull the merged commit into the main working tree (`D:\AureLysn`) using fast-forward only:
   ```bash
   git -C D:/AureLysn pull --ff-only origin main
   ```
4. If the work was done in an external worktree, remove the worktree cleanly:
   ```bash
   git -C D:/AureLysn worktree remove <worktree-path>
   git -C D:/AureLysn worktree prune
   ```
