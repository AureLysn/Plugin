---
name: kiem-tra-he-thong
description: "Run the AureLysn Vault verification gate suite (vault_doctor, vault_index, claim_check, asset_scan) from D:\\AureLysn and interpret exit codes 0/1/2. Use when checking vault health ('kiểm tra hệ thống', 'chạy doctor', 'dựng lại index', 'kiểm tra cổng') or before committing."
---

# `kiem-tra-he-thong` — Vault Verification Gate Suite

## 1. Preconditions & Authoritative Schema

- Authoritative specification: `[[09-gates]]`, `[[index-inclusion-rules]]`, `[[command-reference]]`.
- This skill is the home of the vault's pre-commit gates: `git-guard` `nhanh-va-commit` §2 points here instead of repeating the commands.
- Always execute commands from the vault root (`D:\AureLysn`). Never chain `cd <subfolder> && ...` and never pipe a gate into `tail`/`head` without `pipefail` (`chan_exit_sau_ong.py`).

---

## 2. Gate Execution Sequence

### Step 1 — Rebuild or Verify the Two-Root Search Index
When notes have been added, renamed, or edited, rebuild both index roots first:
```bash
python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
```
**In an external worktree** (`D:\AureLysn-wt\<slug>`) the nested repositories `05_Evasion/` and `04_Portfolio/` are absent: a `--build` there drops their notes from `vault-index.json`, `--check` reports them as drift, and `vault_doctor` reports links into them as broken. Before committing from a worktree, keep the `HEAD` entries of `04_Portfolio/` and `05_Evasion/` in the rebuilt index (or rebuild on `D:\AureLysn` after the merge is pulled), and count only errors in files the branch changed (2026-11-23).

To verify without writing:
```bash
python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --check
```

### Step 2 — Run `vault_doctor.py` (Notes & Templates)
Check all indexed notes (Root 1 + Root 2) and all note templates in `01_Origine/04_Tools/Templates/`:
```bash
python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --templates
```

### Step 3 — Run `claim_check.py` (Paths, Root 1 Isolation & Agents)
Verify storage paths in `[[stores]]`, Root 1 = `0` fiction notes, and subagent/skill references against `[[13-agent-routing]]`:
```bash
python 01_Origine/04_Tools/VaultTool/Validation/claim_check.py --no-scan
```
*(Omit `--no-scan` when performing a full multi-drive duplicate-root scan.)*

### Step 4 — Run `asset_scan.py --check` (When Sidecar Notes Changed)
```bash
python 01_Origine/04_Tools/VaultTool/Organization/asset_scan.py --check
```

---

## 3. Exit Code Handling & Handoff

- `0` = Clean (`Pass`)
- `1` = Non-blocking `Warning` (inspect to confirm no new warning was introduced)
- `2` = Blocking `Error` (**STOP** — fix all errors and re-run before reporting completion; see `[[CLAUDE]]` §2)
- Label all reported counts as `executed` (`[[CLAUDE]]` Invariant 11) and include `- Used: kiem-tra-he-thong` in the handoff block.
