---
name: push-to-translate-center
description: "Sync finalized chapters (status: final) or labeled drafts from a fiction project into Aurel's local reading and translation desk (Nexus / TranslateCenter). Use when syncing chapters to the translation app ('đưa lên trạm dịch', 'đẩy chương lên trạm dịch', 'cập nhật trạm dịch', 'push to translate center')."
---

# `push-to-translate-center` — Sync Chapters to Translation Desk

## 1. Preconditions & Boundaries

- Local translation web app (`Nexus` / `TranslateCenter`) runs at `http://127.0.0.1:8765` (start script: `05_Evasion/03_Subsystems/Nexus/start.bat`).
- **Safety Boundary:** This skill interacts with the translation desk solely via `tram_dich_push.py` CLI calls. Never open or mutate `05_Evasion/03_Subsystems/Nexus/data/library.db` directly.
- Chapters must reside on the **main vault tree** (`D:\AureLysn` on `main`).
- Only `type: chapter` notes under `<Project>/04_Manuscript/chapters/` are pushed (`final` chapters are immutable; drafts are updated when their vault text changes).

---

## 2. Step-by-Step Sync Procedure

1. **Dry Run (Always First):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Scripts/tram_dich_push.py --project <CODE>
   ```
   Inspect the output table:
   - New chapters to add
   - Draft chapters to overwrite (`[GHI DE]`)
   - Title collisions (`[LOI] Nhieu chuong ra cung mot tieu de` → fix by setting `title: "..."` in frontmatter)
2. **Review Warnings with Aurel:**
   Report any `[LOI]` or `[DA SUA SAU KHI DAY]` lines.
3. **Apply After Aurel's Explicit Confirmation:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Scripts/tram_dich_push.py --project <CODE> --apply
   ```
4. **Verify via Second Dry Run:**
   Run `tram_dich_push.py --project <CODE>` again. Confirm it reports:
   `Tram da co du moi chuong (<n> da chot, <n> nhap).`
- Include `- Used: push-to-translate-center` in the handoff block.
