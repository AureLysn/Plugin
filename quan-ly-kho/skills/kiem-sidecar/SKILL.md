---
name: kiem-sidecar
description: "Verify all asset and source sidecars across the vault using asset_scan.py --check: confirms store + path_rel exists on disk, detects uninspected skeletons (seen_at: null), and flags stale sidecars (file_mtime > seen_at). Use when checking storage links ('kiểm sidecar', 'kiểm tra path_rel', 'asset_scan --check')."
---

# `kiem-sidecar` — Sidecar Integrity & `path_rel` Verification

## 1. What This Gate Checks (`[[11-asset-index]]`)

`vault_doctor.py` validates YAML frontmatter syntax, but does **not** open the stores (on Drive, `[[stores]]`) to check whether binary files exist. `asset_scan.py --check` closes that gap across every note containing an `asset:` block (`type: asset` and `type: source`):
1. **`[STORE LA]` (`exit 2`):** `asset.store` is not declared in `[[stores]]` (`01_Origine/03_Systems/Config/stores.md`).
2. **`[PATH_REL RONG]` (`exit 2`):** `store + path_rel` does not resolve to an existing file on disk.
3. **`[CU HON FILE GOC]` (`exit 1`):** `file_mtime > seen_at` — the binary file was modified after the sidecar was written.
4. **`[chua mo file goc]`:** `seen_at: null` — skeleton awaiting inspection (`viet-sidecar`).

---

## 2. Execution & Remediation

1. Run from the vault root (`D:\AureLysn`):
   ```bash
   python 01_Origine/04_Tools/VaultTool/Organization/asset_scan.py --check
   ```
2. If `[PATH_REL RONG]` appears:
   - Check whether the drive declared in `[[stores]]` is mounted (`claim_check.py --no-scan`).
   - If the binary file was renamed or moved inside its store, update `asset.path_rel` (and `asset.store` if moved across branches) in the sidecar note.
   - Never delete a broken sidecar silently (`[[AGENTS]]` Invariant 3).
- Include `- Used: kiem-sidecar` in the handoff block.
