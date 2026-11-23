---
name: viet-sidecar
description: "Fill out a binary asset sidecar note (type: asset; the folder cards are in 02_Storage/<branch>/, skeletons from asset_scan.py at the store's sidecar destination in stores.md) after inspecting the real file or metadata. Use when completing a draft sidecar ('viết sidecar', 'điền sidecar', 'hoàn thiện thẻ asset')."
---

# `viet-sidecar` — Authoring & Completing Binary Asset Sidecars

## 1. Core Honesty Rule (`[[11-asset-index]]` & `[[CLAUDE]]` Invariant 5)

- **Never guess or fabricate visual contents, dimensions, color modes, or layer structures from a filename alone.**
- A sidecar may transition from `status: draft` (`seen_at: null`) to `status: final` (`seen_at: YYYY-MM-DD`) **only** when the underlying file or preview has actually been inspected (by Aurel, by reading exported PNG/JPG previews, or via deterministic metadata tools like `exiftool`, `ffprobe`, or `font_cards.py`).

---

## 2. Step-by-Step Procedure

1. **Read the existing sidecar note first (`[[CLAUDE]]` Invariant 4).** Where to find it: the card of a store folder sits beside that folder's mirror in the vault's `02_Storage/<branch>/` (all 50 `type: asset` cards on 2026-11-13); a skeleton made by `quet-kho` is at the store's sidecar destination in `[[stores]]` §2 (`03_Atelier/02_Asset_Catalog/` for `shared-bulk`, which holds no card yet). The file it describes is on the Drive store, never in the vault.
2. **Extract deterministic technical metadata (`executed`):**
   - Images / PSD / AI / PDF: `exiftool <file>` (dimensions, color space, DPI, page/layer count)
   - Video / Audio: `ffprobe -hide_banner <file>` (resolution, codec, fps, duration, sample rate)
   - Fonts: `python 01_Origine/04_Tools/VaultTool/Organization/font_cards.py` (`fonttools` / `ttx` glyph & Vietnamese coverage check)
3. **Populate frontmatter (`[[11-asset-index]]`):**
   - Keep `asset.store` and `asset.path_rel` relative to `[[stores]]` (never write a drive letter in the sidecar).
   - Set `license:` from the list in `[[01-frontmatter]]` §6 (`commercial-ok` | `personal-only` | `attribution-required` | `editorial-only` | `reference-only` | `unknown` | `own-work` | `client-work`). A CC0 or purchased commercial licence is `commercial-ok`; CC-BY is `attribution-required`. `reference-only` assets cannot be embedded in deliverables (`[[11-asset-index]]` §3.1).
   - Update `seen_at: YYYY-MM-DD`, `status: final`, and `last_updated: YYYY-MM-DD` via `vaultlib.write_keep_eol()`.
4. **Verify via `kiem-sidecar` (`asset_scan.py --check`) and `vault_doctor.py`.**
- Include `- Used: viet-sidecar` in the handoff block.
