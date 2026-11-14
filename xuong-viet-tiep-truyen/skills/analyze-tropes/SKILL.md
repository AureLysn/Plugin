---
name: analyze-tropes
description: "Analyze genre conventions, trope expectations, and reader promises of a fiction project, linking to 01_Origine/02_Knowledge/Curated_Notes/writing/structure/. Use when mapping a story's genre DNA ('phân tích trope', 'analyze-tropes', 'quy ước thể loại')."
---

# `analyze-tropes` — Genre Conventions, Tropes & Reader Promises

## 1. Preconditions & Reference Knowledge

- Read `shared/vault-config.md` and the relevant structure/genre notes in `01_Origine/02_Knowledge/Curated_Notes/writing/structure/`:
  - `[[chinese-webnovel-chapter-conventions]]`, `[[japanese-web-novel-conventions]]`, `[[ao3-ratings-and-archive-warnings]]`
  - `[[detective-fair-play]]`, `[[romance-central-love-story]]`, `[[loop-narrative]]`, `[[frame-narrative]]`, `[[braided-multiple-pov]]`

---

## 2. Step-by-Step Procedure

1. **Identify Core Trope Pillars (`inspected`):**
   From the source text, tags, and author comments (`type: source`), classify:
   - **Core Premise & Hook:** What drew readers to this story in Chapter 1?
   - **Obligatory Scenes & Payoffs:** Which genre beats must occur for the continuation to feel authentic (`[[setup-and-payoff]]`)?
   - **Hard Anti-Tropes (`forbid`):** Which tropes or tone shifts would betray the original work's promise?
2. **Record in `<Project>/00_Overview/` (or `03_Development/arcs/`):**
   Write or update the trope & genre analysis note with explicit `source.ref` citations to chapters and author notes (`[[AGENTS]]` Invariant 5).
3. **Rebuild index and verify links:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   ```
- Include `- Used: analyze-tropes` in the handoff block.
