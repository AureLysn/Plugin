---
name: snapshot-va-sao-luu
description: "Create a dated zip snapshot of AureLysn Vault via snapshot.ps1 and verify the Google Drive offsite mirror under the 3-2-1 backup rule. Use when user asks to 'snapshot', 'sao lưu', 'backup zip', or before major structural migrations."
---

# `snapshot-va-sao-luu` — 3-2-1 Vault Snapshot & Mirror Verification

## 1. Preconditions & Authoritative Rules

- Authoritative rules: `[[backup-and-recovery]]`, `[[stores]]` (`01_Origine/03_Systems/Config/stores.md`), `[[snapshot-backup-workflow]]` (`01_Origine/04_Tools/Workflows/update/snapshot-backup-workflow.md`).
- Always run from the **main vault tree** (`D:\AureLysn` on `main`), never from inside a temporary worktree.

---

## 2. Step-by-Step Procedure

1. **Verify `stores.md` snapshot keys:**
   Inspect `01_Origine/03_Systems/Config/stores.md` (`§3`) to confirm `snapshot-to:` points to the Drive snapshot folder and that Drive is mounted (the zip is written to Drive directly).
2. **Run `snapshot.ps1` in PowerShell:**
   ```powershell
   . D:\AureLysn\01_Origine\04_Tools\VaultTool\Scripts\snapshot.ps1; snapshot
   ```
3. **Verify the self-check output (`[[principles]]` Principle 5):**
   Confirm the script prints:
   - `[XONG] ...\AureLysn_<YYYY-MM-DD_HHmm>.zip` with `vault/ : <N> file` (`N > 0`, and no `> 10%` drop compared to the previous snapshot).
   - The zip itself is on Drive; check that it has finished syncing.
   - Zero `ROBOCOPY HONG` (`exit >= 8`) errors.

---

## 3. Handoff & Audit Trail

- Report the exact `.zip` filename, size in MB, file count inside `vault/`, and whether Drive has synced it, with the **`executed`** label.
- Include `- Used: snapshot-va-sao-luu` in the handoff summary.
