---
name: quet-kho
description: "Scan a binary folder of a store (on Drive, by store id) using asset_scan.py to preview and generate Markdown sidecar skeletons (type: asset). Use when cataloging a new project or asset pack of a store ('quét kho', 'tạo khung sidecar', 'asset_scan')."
---

# `quet-kho` — Binary Storage Scanning & Sidecar Skeleton Generation

## 1. Preconditions & Granularity Check

Before running `asset_scan.py`, check `[[storage-cataloging-plan]]` and `[[11-asset-index]]` so you do **not** flood the vault with per-file stubs:
- **`03_Finished_Work/` (`work-archive`):** Cataloged at **1 note per project** in `04_Portfolio/` or `03_Atelier/04_Projects/` (use `project_cards.py` or `Case-Study-Note.md`), not per render frame.
- **`02_Assets/` (`shared-bulk`):** Cataloged at **1 sidecar note per pack or font family**. `asset_scan.py --apply` writes these skeletons to `03_Atelier/02_Asset_Catalog/` (no card there yet on 2026-11-13); the existing cards are the folder cards in the vault's `02_Storage/02_Assets/<folder>/`. Check both before creating one, so a pack does not get two cards.
- **Two places, two names:** the **files** are in the store on Drive, named by store id (`[[stores]]`); the vault's `02_Storage/<branch>/` mirrors the folder tree and holds **cards only**.
- **`01_Personal_Archive/` (`personal-bulk`):** Cataloged only when cited as Style DNA evidence (`[[artwork-observations-20260910]]`) or as a primary story source (`type: source`).

---

## 2. Step-by-Step Procedure

1. **Verify store mount in `[[stores]]` (`01_Origine/03_Systems/Config/stores.md`):**
   Confirm the target store ID (`work-archive`, `shared-bulk`, `personal-bulk`) is mounted.
2. **Run `asset_scan.py` in preview mode first (no `--apply`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Organization/asset_scan.py --store <store-id> --path "<folder-path>"
   ```
   Review the printed list of candidate sidecars and total byte size with Aurel.
3. **Apply when confirmed:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Organization/asset_scan.py --store <store-id> --path "<folder-path>" --apply
   ```
   *(Generated skeletons carry `status: draft` and `seen_at: null` until filled via `viet-sidecar`.)*
4. **Rebuild index and run doctor:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   ```
- Include `- Used: quet-kho` in the handoff block.
