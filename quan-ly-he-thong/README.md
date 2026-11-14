# `quan-ly-he-thong` — AureLysn Vault System Administration

System administration plugin for **`D:\AureLysn`** (`01_Origine/`, `06_Station/`, and vault-wide verification gates).
*(General Git skills and Bash safety hooks live in the companion plugin **`git-chung`**.)*

---

## 1. Components

| Type | Name | Path | Role |
|---|---|---|---|
| **Skill** | `kiem-tra-he-thong` | `skills/kiem-tra-he-thong/SKILL.md` | Runs the vault gate suite (`vault_doctor`, `vault_index`, `claim_check`, `vault_report`) from `D:\AureLysn` |
| **Skill** | `snapshot-va-sao-luu` | `skills/snapshot-va-sao-luu/SKILL.md` | Executes `snapshot.ps1` and verifies the zip written to Google Drive |
| **Skill** | `ban-giao` | `skills/ban-giao/SKILL.md` | End-of-session handoff workflow updating `[[session-handoff]]` and `[[open-items-dashboard]]` |
| **Skill** | `ghi-loi` | `skills/ghi-loi/SKILL.md` | Converts discovered tool traps or recurring errors into `PreToolUse` hooks, gates, or entries in `[[pre-handoff-verification-checklist]]` and `[[ai-tool-and-environment-quirks]]` |
| **Subagent** | `do-trang-thai` | `agents/do-trang-thai.md` | Isolated read-only subagent (`sonnet`, `low` effort) that runs all system measurement commands and returns a compact status table |
| **Hook** | `chan_commit_index_cu.py` | `hooks/chan_commit_index_cu.py` (+ `test_chan_commit_index_cu.py`) | `PreToolUse` hook on `Bash` that blocks `git commit` when staged `.md` notes are newer than `vault-index.json` (`vault_index.py --check`) |

## Two hook configs, one per agent host

- `hooks/hooks.json` uses `${CLAUDE_PLUGIN_ROOT}` paths and is the config Claude Code loads.
- `hooks.json` at the plugin root uses relative `python hooks/<name>.py` commands and serves Google Antigravity (Aurel, 2026-11-13).
- The hook scripts in `hooks/` are the single source; both configs must list the same scripts. Change both in the same edit.
