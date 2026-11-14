# `git-chung` — Safe Git Operations & PreToolUse Guards

General-purpose Git safety plugin for **all repositories** on Aurel's workstation (the vault root `D:\AureLysn`, a repository since 2026-11-12, the two app repositories in `01_Origine/03_Systems/`: `Atelier`, `AureLysnOS`, and the two zone repositories `05_Evasion/` and `04_Portfolio/`, the latter holding the website code in `Portfolio_Web/`). Its skills work in any Git repository; `nhanh-va-commit` and `git-cuu-ho` name vault paths (`01_Origine/04_Tools/VaultTool/…`, `01_Origine/05_Meta/Index/vault-index.json`) only in the steps that apply when the repository is the vault.

---

## 1. Skills (`4` Skills)

| Skill | Purpose |
|---|---|
| `git-an-toan` | Pre-flight Git inspection, `.git/index.lock` checks, line-ending protection, worktree placement outside the main tree, and destructive-command prohibitions |
| `nhanh-va-commit` | Branch naming (`loai/mo-ta-ngan`), explicit file staging (never `git add -A`), pre-commit gate execution when `AGENTS.md` + `01_Origine/` exist, and `git diff --stat` line-ending verification |
| `pr-va-merge` | For all five repositories, once at the close of a session (Aurel, 2026-11-14). Pushing feature branches, opening GitHub PRs via `gh`, inspecting CI checks, and merging safely without mutating the main working tree |
| `git-cuu-ho` | Recovering from mid-session Git faults: stale `index.lock`, wrong-branch commits, CRLF/LF full-file diffs, merge conflicts, and `git reflog` recovery |

---

## 2. `PreToolUse` Bash Safety Hooks (`5` Hooks + `5` Unit Test Suites)

Every hook intercepts `Bash` tool calls before execution (`exit 0` = allow, `exit 2` = block with explanation on `stderr`):

| Hook Script | Test Suite | What It Blocks & Why |
|---|---|---|
| `hooks/chan_git_mv.py` | `hooks/test_chan_git_mv.py` | Blocks `git mv` on Markdown notes (`*.md`) — renaming outside Obsidian leaves inbound wikilinks pointing to the old filename (`[[10-skill-authoring]]` · `[[AGENTS]]` Invariant 10). |
| `hooks/chan_sed_i.py` | `hooks/test_chan_sed_i.py` | Blocks `sed -i` / `sed --in-place` — Git Bash `sed -i` strips `CR` on Windows, turning a 3-line edit into a full-file diff in a repository that does not normalise line endings (the vault's `.gitattributes` stores six text types as `LF`) (`[[ai-tool-and-environment-quirks]]`). |
| `hooks/chan_nhap_temp.py` | `hooks/test_chan_nhap_temp.py` | Blocks creating or executing temporary scripts inside `$TEMP`, `/tmp` or `AppData/Local/Temp`. The session scratchpad (a path with a `scratchpad` folder) is allowed; that is where scratch scripts go (Aurel, 2026-11-13). |
| `hooks/chan_exit_sau_ong.py` | `hooks/test_chan_exit_sau_ong.py` | Blocks piping a command into a filter followed by `; echo $?` (`cmd \| tail; echo $?`), which prints the filter's exit code (`0`) and hides gate failures (`exit 2`). |
| `hooks/chan_checkout_cay_chinh.py` | `hooks/test_chan_checkout_cay_chinh.py` | Blocks branch-switching commands (`git checkout <branch>`, `git switch`, `gh pr checkout`) on the main vault tree (`D:\AureLysn`) while allowing single-file restores (`git checkout -- <file>`) and isolated worktrees. |

## Two hook configs, one per agent host

- `hooks/hooks.json` uses `${CLAUDE_PLUGIN_ROOT}` paths and is the config Claude Code loads.
- `hooks.json` at the plugin root uses relative `python hooks/<name>.py` commands and serves Google Antigravity (Aurel, 2026-11-13).
- The hook scripts in `hooks/` are the single source; both configs must list the same scripts. Change both in the same edit.
