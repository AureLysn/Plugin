---
name: sap-xep-file
description: "Triage binary files from the store inbox on Drive (kho-cloud-inbox), standardize filenames per naming-conventions.md, update sidecar path_rel pointers, and stage retired files in the store's _to_delete folder on Drive. Use when organizing storage files ('sắp xếp file', 'dọn inbox kho', 'đổi tên file kho', 'chuyển sang _to_delete')."
---

# `sap-xep-file` — Binary Storage Triage, Naming & Safe Archiving

## 1. Authoritative Rules

- Naming standard: `[[naming-conventions]]` (`<Domain>-<Project>_<Item>_<Stage>_<Version>.<ext>` for binary assets).
- Lane & store routing: `[[04-lanes]]` and `[[stores]]` (`01_Origine/03_Systems/Config/stores.md`).
- Safe retirement: `[[backup-and-recovery]]` §1 (`_to_delete\<YYYY-MM-DD>\` on the Drive store, beside the five branches — never `rm` directly). Both staging folders are on Drive, resolved through `[[stores]]` §3 (`kho-cloud-inbox` → `00_Inbox`); the vault's `02_Storage/` holds cards only.

---

## 2. Step-by-Step Procedure

1. **Classify `lane` first (`[[AGENTS]]` §0 & §2):**
   The file goes to the **store** (a folder on Drive, resolved by its id in `[[stores]]`). The vault folder of the same branch name, `02_Storage/<branch>/`, receives only the card.
   - `work` → store `work-archive` (branch `03_Finished_Work`)
   - `personal` (illustrations, personal archives, fiction primary sources) → store `personal-bulk` (branch `01_Personal_Archive`)
   - `personal` (reading novels / fanfic `.epub`/`.txt`/`.html`) → store `library` (branch `05_Library`)
   - `shared` (reusable fonts, brushes, SFX, textures) → store `shared-bulk` (branch `02_Assets`)
   - `shared` (moodboards / visual benchmarks) → store `project-refs` (branch `04_References`)
   - **If `lane` is uncertain:** Stop and ask Aurel; leave the file in the store inbox.
2. **Preview renames and moves before executing:**
   Present a table of `Old Path → New Path` to Aurel before moving batches of files.
3. **Update any affected sidecar notes in the same step:**
   If a binary file already has a sidecar note (`type: asset` or `type: source`), update `asset.store` and `asset.path_rel` immediately and verify with:
   ```bash
   python 01_Origine/04_Tools/VaultTool/Organization/asset_scan.py --check
   ```
4. **Retiring duplicate or superseded binaries:**
   Move retired binaries to `_to_delete\<YYYY-MM-DD>\` on the Drive store (never into the Git-tracked markdown vault tree). Permanent deletion is performed only by Aurel (`[[AGENTS]]` Invariant 3).
- Include `- Used: sap-xep-file` in the handoff block.
