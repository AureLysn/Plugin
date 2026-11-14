---
name: init-project
description: "Initialize a new fiction continuation or original story project in 05_Evasion/01_Oeuvre/Studio/ (Continue/ or Original/) with canonical subfolders, the project note <CODE>.md, and 02_Story_Bible/style/ skeletons. Use when starting a new story project ('khởi tạo dự án truyện', 'tạo project mới', 'init-project')."
---

# `init-project` — Initialize a Fiction Studio Project

## 1. Preconditions & Inputs

- Read `shared/vault-config.md`, `[[id-conventions]]`, `[[01-frontmatter]]`, and `[[04-lanes]]`.
- Confirm with Aurel:
  1. **Studio branch:** `Studio/Continue/` (continuation/fanfic) or `Studio/Original/` (original work).
  2. **Project code & folder name:** `<CODE>_<slug>` (uppercase code `2–6` letters, lowercase kebab-case slug without diacritics, e.g., `PPCT_phan-phai-chien-tranh`, per `[[id-conventions]]`).
  3. **Source universe(s):** `<UNIVERSE>` code(s) in `05_Evasion/01_Oeuvre/Database/Fandom/` (or `original`).

---

## 2. Step-by-Step Procedure

1. **Verify no code collision exists:**
   Check existing folders in `05_Evasion/01_Oeuvre/Studio/Continue/` and `Studio/Original/` via `project_table.py`.
2. **Create the canonical directory tree (`shared/vault-config.md` §2):**
   - `00_Overview/`
   - `01_Project-canon/` (`sources/`, `notes/`) with `source-index.md`
   - `02_Story_Bible/` (`characters/`, `locations/`, `organizations/`, `relationships/`, `secrets/`, `style/`, `world-rules/`)
   - `03_Development/` (`arcs/`, `structure/`, `timeline/`, `tracker/`)
   - `04_Manuscript/` (`chapters/`)
   - `05_Management/` (`crosscheck/`, `decisions/`, `inbox/`, `questions/`, `snapshots/`)
   - `06_Alternate_Versions/` (`branches/`)
   Copy the skeleton `Studio/<Continue|Original>/[CODE] Project_Name/` rather than building the tree by hand.
3. **Instantiate core notes from `01_Origine/04_Tools/Templates/`:**
   - `00_Overview/<CODE>.md` (`id: project.<code>`, `type: project`, `scope: project`, `project: <CODE>`, `lane: personal`, `status: active`) from `Templates/project/Project-Note.md`.
   - `02_Story_Bible/style/targets.md` and `02_Story_Bible/style/ai-tells.md` (with machine-readable `gate:` YAML block) from `Templates/story_development/Style-Note.md`.
4. **Rebuild index and run gates:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   ```
- Include `- Used: init-project` in the handoff block.
