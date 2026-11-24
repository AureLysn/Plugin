---
name: snapshot-va-sao-luu
description: "Create a dated zip snapshot of AureLysn Vault via snapshot.ps1, prove that it restores with snapshot_drill.py, and verify the Google Drive offsite mirror under the 3-2-1 backup rule. Use when user asks to 'snapshot', 'sao lưu', 'backup zip', 'diễn tập khôi phục', or before major structural migrations."
---

# `snapshot-va-sao-luu` — 3-2-1 Vault Snapshot, Restore Drill & Mirror Verification

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
   - `[DONE] ...\AureLysn_<YYYY-MM-DD_HHmm>.zip` with `vault/ : <N> files` (`N > 0`, and no `> 10%` drop compared to the previous snapshot).
   - The zip itself is on Drive; check that it has finished syncing.
   - Zero `ROBOCOPY FAILED` (`exit >= 8`) errors.
4. **Run the restore drill (`snapshot_drill.py`, since 0.10.0, `[[plugin-benchmark-20261124]]` V7):**
   A file count does not prove that the zip restores. From `D:\AureLysn`:
   ```bash
   python 01_Origine/04_Tools/VaultTool/Scripts/snapshot_drill.py
   ```
   It reads back every entry of the newest zip in `snapshot-to` (the CRC is checked on each read) and compares the content with the vault. `--into "<session scratchpad>"` also writes the files out, as a restore would, and removes them afterwards unless `--keep`; a folder inside the vault is refused. `--zip <file>` checks another snapshot.
   - Exit `0`: every file reads back and matches. Expected right after a snapshot.
   - Exit `1`: only expected differences (`newer`, `added`, `gone`, `moved`), because the vault changed after the snapshot. Normal for an older zip.
   - Exit `2`: `CORRUPT`, `DIFFERS` or `MISSING` files, or no zip found. Do not rely on that snapshot: keep the earlier zips, tell Aurel, take a new one.

   Reading 12,925 entries took 4 min 22 s (executed 2026-11-24), longer than the default command timeout: run it in the background or raise the timeout.

---

## 3. Handoff & Audit Trail

- Report the exact `.zip` filename, size in MB, file count inside `vault/`, the drill's exit code and count line, and whether Drive has synced it, with the **`executed`** label.
- Include `- Used: snapshot-va-sao-luu` in the handoff summary.
