# `quan-ly-kho` — Binary Storage (`02_Storage/`) & Sidecar Management

Plugin governing binary asset cataloging, sidecar verification, and file organization across the five stores on Drive (`~38 GB`, `[[stores]]`) and their cards in the vault: the folder cards in **`02_Storage/<branch>/`** and the skeleton destinations named in `[[stores]]` §2 (**`03_Atelier/02_Asset_Catalog/`** for `shared-bulk`, empty on 2026-11-13).

---

## 1. Skills (`4` Skills)

| Skill | Script / Schema Used | Purpose |
|---|---|---|
| `quet-kho` | `01_Origine/04_Tools/VaultTool/Organization/asset_scan.py` · `[[stores]]` · `[[storage-cataloging-plan]]` | Scans a binary folder of a store (dry-run first, then `--apply`) to generate `type: asset` sidecar skeletons |
| `viet-sidecar` | `[[11-asset-index]]` · `01_Origine/04_Tools/VaultTool/Organization/font_cards.py` | Fills out sidecar notes (`status: draft` → `final`, `seen_at`, `license`, and 4 body sections) ONLY after inspecting the real asset |
| `kiem-sidecar` | `asset_scan.py --check` · `claim_check.py` | Verifies every `store + path_rel` resolves on disk, catches uninspected skeletons (`seen_at: null`), and flags stale sidecars (`file_mtime > seen_at`) |
| `sap-xep-file` | `[[naming-conventions]]` · `[[backup-and-recovery]]` | Standardizes binary filenames (`<Domain>-<Project>_<Item>_<Stage>_<Version>.<ext>`), routes files from the store inbox on Drive by `lane`, and stages retired binaries in the store's `_to_delete\` on Drive |
