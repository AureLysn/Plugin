---
name: ingest-sources
description: "Register primary source files kept in the stores personal-bulk or library, create type: source sidecar notes in 01_Project-canon/sources/, and initialize the reading ledger inside the source note. Use when importing raw novel text, epubs, or author notes into a story project ('nhập nguồn', 'ingest-sources', 'đăng ký nguyên tác')."
---

# `ingest-sources` — Source Registration & Reading Ledger Setup

## 1. Preconditions & Rules

- Read `shared/vault-config.md`, `[[11-asset-index]]`, `[[index-inclusion-rules]]` §2, and `[[reading-ledger-rule]]`.
- **Hard Rule:** Raw uncurated dumps (`.txt`, `.epub`, `.html`, `.pdf`) live in the store `personal-bulk` (cards in `02_Storage/01_Personal_Archive/`) or the store `library` (cards in `02_Storage/05_Library/`) — **never** inside the Git-tracked vault tree (`05_Evasion/01_Oeuvre/`).

---

## 2. Step-by-Step Procedure

1. **Locate and verify the binary/raw source file in its store:**
   Confirm the exact relative path under `personal-bulk` or `library` (`[[stores]]`). The file is on the Drive store; the vault's `02_Storage/` holds its card only.
2. **Create a curated `type: source` note in `<Project>/01_Project-canon/sources/`:**
   Use `01_Origine/04_Tools/Templates/project/Source-Note.md`:
   - `id: source.<CODE>.<slug>`
   - `type: source`, `scope: project`, `project: <CODE>`, `lane: personal`, `canon_layer: fic_explicit` (or `official_canon`)
   - Populate `asset.store`, `asset.path_rel`, `asset.bytes`, `asset.file_mtime`, and `asset.seen_at`.
3. **Initialize the Reading Ledger inside the source note itself (`[[reading-ledger-rule]]`):**
   - The ledger is the coverage section of `<Project>/01_Project-canon/sources/<source>.md` (`## Phạm vi đã trích xuất` in `Source-Note.md`); a source read across several notes keeps its table in `sources/_MOC.md`. No project has a separate `reading-ledger.md`.
   - Divide the source into chapters/segments (`ch01`..`chNN`) with status columns (`unread` · `inspected` · `extracted`) so multi-session extraction never skips or fabricates chapters.
4. **Run verification gates:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Organization/asset_scan.py --check
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   ```
- Include `- Used: ingest-sources` in the handoff block.
