---
name: pr-va-merge
description: "Push feature branches, open GitHub Pull Requests via gh CLI, verify CI checks, merge into main, and clean up worktrees, in any of the vault or app repositories. Use when user asks to 'tạo PR', 'merge nhánh', 'gộp vào main', 'push lên GitHub', or clean up after a PR."
---

# `pr-va-merge` — Pull Request Creation, Merge & Worktree Cleanup

## 0. Where This Skill Applies

- It needs a remote named `origin` and the `gh` CLI. Check first: `git remote -v`.
- It applies to all six repositories (`git-an-toan` §1.3): the vault root, `05_Evasion/`, `04_Portfolio/`, `Atelier`, `AureLysnOS` and `AureLysn/Plugin`. `AureLysn/Plugin` has no main tree: its branch is made in a fresh clone at each plugin release (`[[_SYSTEMS-MOC]]` §4.3), so §3 steps 3–4 do not apply there.
- Three of them are public. Before any push, §1 step 4 checks the remote and scans a push to a public one.
- **When:** once, at the close of the session, after the gates pass (`git-an-toan` §1.4) — not after each commit. In the vault this is step 7 of `[[session-handoff-workflow]]`, after `vault-ops` `ban-giao`.
- The `D:/AureLysn` lines in §3 are written for the root repository; for another repository, use its own main tree (`D:/AureLysn/05_Evasion`, `D:/AureLysn/04_Portfolio`, or the app folder).

---

## 1. Preconditions Before Pushing

1. Confirm all commits on the branch passed the repository's verification gates (`nhanh-va-commit` §2).
2. Fetch the latest `origin/main` and check whether `main` has advanced:
   ```bash
   git fetch origin main
   git log HEAD..origin/main --oneline
   ```
3. If `origin/main` has new commits, rebase or merge `origin/main` into the feature branch inside the worktree and re-run the repository's gates (`nhanh-va-commit` §2; for the vault, `vault-ops` `kiem-tra-he-thong`).
4. **Disclosure scan before a push to a public remote** (Aurel, 2026-11-28; `[[14-safety]]` §2). A pushed branch is public at once, before any merge, and a disclosure cannot be taken back. Routine pushes are allowed; a new disclosure needs this scan and Aurel's choice first. Check the remote:
   ```bash
   gh repo view --json visibility --jq .visibility
   ```
   `PRIVATE`: go on to §2. `PUBLIC` (on 2026-11-28: `AureLysn/Evasion`, `AureLysn/Portfolio`, `AureLysn/Plugin`): read everything the push adds, commit authors and messages included:
   ```bash
   git diff --stat origin/main...HEAD
   git diff origin/main...HEAD
   git log --format='%h %an <%ae> | %cn <%ce>%n%B' origin/main..HEAD
   ```
   Look for a new disclosure: personal data (names, e-mail addresses, phone numbers, postal addresses), keys and tokens (never allowed anywhere, `[[14-safety]]` §1), local machine paths (a user profile folder, drive-letter paths, the Drive mount), unpublished work and client information. A first pass that prints each hit under its file:
   ```bash
   git diff -U0 origin/main...HEAD | grep -i -E '^\+\+\+ |^\+.*(@[a-z0-9-]+\.[a-z]{2,}|\b[a-z]:[/\]|users[/\]|appdata|token|secret|passw|api.?key)'
   ```
   Binary files (`Bin` in `--stat`) cannot be read this way: say what each one holds. A hit is new when `origin/main` does not hold it yet (`git grep -n -F '<hit>' origin/main`; for an author e-mail, `git log --format=%ae origin/main`). The PR title and body become public too, so write them from the scanned diff.
   - Nothing new: the push is routine; go on to §2.
   - Something new: stop before the push, tell Aurel what would become public (file, line, what it reveals) and push only after Aurel's choice.
   - A plugin sync to `AureLysn/Plugin` always stops here for Aurel's choice and also looks for project codes (`[[_SYSTEMS-MOC]]` §4.3).

---

## 2. Pushing & Opening the Pull Request (`gh pr create`)

1. Push the branch to `origin` (for a public remote, only after §1 step 4):
   ```bash
   git push -u origin HEAD
   ```
2. Create the PR with a structured summary and verification section:
   ```bash
   gh pr create --base main --title "<concise title>" --body "## Tóm tắt thay đổi
   - ...

   ## Xác minh (Verify gate)
   - [x] vault_doctor --include-fiction (executed: 0 lỗi)
   - [x] vault_index --check (executed: khớp)
   - [x] quét công bố, chỉ với remote public (executed: không có gì mới / Aurel chọn …)"
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
4. If the work was done in an external worktree, remove it cleanly. Nested checkouts (`git-an-toan` §4.2) go first, each in its own command. If one is refused (uncommitted files), stop: removing the outer worktree would delete it anyway, without `--force` (`chan_git_pha_huy.py` asks in that case):
   ```bash
   git -C D:/AureLysn/04_Portfolio worktree remove <worktree-path>/04_Portfolio
   ```
   ```bash
   git -C D:/AureLysn/05_Evasion worktree remove <worktree-path>/05_Evasion
   ```
   Then the worktree itself:
   ```bash
   git -C D:/AureLysn worktree remove <worktree-path>
   git -C D:/AureLysn worktree prune
   ```
