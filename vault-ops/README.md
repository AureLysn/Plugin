# `vault-ops` — AureLysn Vault System Administration

System administration plugin for **`D:\AureLysn`** (`01_Origine/`, `06_Station/`, and vault-wide verification gates).
*(General Git skills and Bash safety hooks live in the companion plugin **`git-guard`**.)*

---

## 1. Components

| Type | Name | Path | Role |
|---|---|---|---|
| **Skill** | `kiem-tra-he-thong` | `skills/kiem-tra-he-thong/SKILL.md` | Runs the vault gate suite (`vault_doctor`, `vault_index`, `claim_check`, `vault_report`) from `D:\AureLysn` |
| **Skill** | `snapshot-va-sao-luu` | `skills/snapshot-va-sao-luu/SKILL.md` | Executes `snapshot.ps1`, verifies the zip written to Google Drive and proves that it restores (`snapshot_drill.py`) |
| **Skill** | `ban-giao` | `skills/ban-giao/SKILL.md` | End-of-session handoff workflow updating `[[session-handoff]]` and `[[open-items-dashboard]]` |
| **Skill** | `ghi-loi` | `skills/ghi-loi/SKILL.md` | Converts discovered tool traps or recurring errors into hook rule notes, gates, `PreToolUse` hooks, or entries in `[[pre-handoff-verification-checklist]]` and `[[ai-tool-and-environment-quirks]]` |
| **Subagent** | `do-trang-thai` | `agents/do-trang-thai.md` | Isolated read-only subagent (`sonnet`, `low` effort) that runs all system measurement commands and returns a compact status table |
| **Hook** | `chan_commit_index_cu.py` | `hooks/chan_commit_index_cu.py` (+ `test_chan_commit_index_cu.py`) | `PreToolUse` hook on `Bash` and `PowerShell` that blocks `git commit` when the index of the repository being committed is stale (`vault_index.py --check`). Since 0.10.0 it also sees commits handed to another program (`bash -c`, `powershell -Command`, an `if { }` body, …) and blocks unreadable input when `GIT_GUARD_STRICT=1` is set (`[[plugin-benchmark-20261124]]` N5) |
| **Hook** | `chay_luat.py` | `hooks/chay_luat.py` (+ `test_chay_luat.py`) | Rule engine (0.10.0, `[[plugin-benchmark-20261124]]` V2): before every shell command and file edit it runs the hook rules written as notes in `01_Origine/05_Meta/Rules/hook/` (format: `[[hook-rule-format]]`), read from the vault's main tree. Draft rules are only logged (`${CLAUDE_PLUGIN_DATA}/luat-hook.jsonl`, no command or file text); active ones warn, ask or block. A rule that cannot be read, or an ask or block rule that hits an everyday call, is skipped and reported; a regex that runs away ends the hook without a decision. Also `--check`, `--try`, `--stats` |
| **Hook** | `nhac_ban_giao.py` | `hooks/nhac_ban_giao.py` (+ `test_nhac_ban_giao.py`) | `SessionStart` and `PreCompact` hook (0.10.0, `[[plugin-benchmark-20261124]]` V1): at session start it points to `[[session-handoff]]` with the branch, uncommitted files and other worktrees; it names hook rules that `chay_luat.py --check` would report; before a compaction it lists what the summary must keep and reminds of `ban-giao`. Pointers only, never note content; it never blocks and is silent outside the vault |
| **Modules** | `tach_lenh.py`, `duong_dan.py` | `hooks/` (+ `test_ban_sao.py`) | Byte-identical copies of the `git-guard` modules that unwrap commands, hold the fail mode and follow paths (installed plugins cannot import from each other). Edit the original in `git-guard/hooks/`, then copy it; the test fails while they differ |

## Two hook configs, one per agent host

- `hooks/hooks.json` uses `${CLAUDE_PLUGIN_ROOT}` paths and is the config Claude Code loads.
- `hooks.json` at the plugin root uses relative `python hooks/<name>.py` commands and serves Google Antigravity (Aurel, 2026-11-13).
- The hook scripts in `hooks/` are the single source; both configs must list the same `PreToolUse` scripts. Change both in the same edit. `nhac_ban_giao.py` is in the Claude Code config only: `SessionStart` and `PreCompact` are Claude Code events, and whether Antigravity has an equivalent was not checked. The same holds for the file-tool entry of `chay_luat.py` (`Write|Edit|MultiEdit|NotebookEdit`): on Antigravity it sees shell commands only.
- Save both configs as UTF-8 **without BOM**. Claude Code rejects a `hooks.json` that starts with a BOM (`JSON Parse error: Unrecognized token`) and loads none of the plugin's hooks; the BOM sat in both plugins from 2026-11-14 until 2026-11-23 (`claude plugin list` showed `failed to load`).
