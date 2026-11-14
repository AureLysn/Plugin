---
name: fanart-prompt
description: "Generate structured, source-grounded image generation prompts from vault character, costume, and scene notes, clearly tagging canon details [note] vs AI additions [added]. Use when creating visual prompts for characters or scenes ('tạo prompt fanart', 'mô tả ảnh cho nhân vật', 'fanart-prompt')."
---

# `fanart-prompt` — Grounded Visual Prompt Generation

## 1. Provenance Tagging Invariant (`[[AGENTS]]` Invariant 5)

Every visual detail in the prompt must be tagged inline so Aurel can immediately distinguish canonical character appearance from AI invention:
- **`[note]`:** Verified attribute from a vault character, costume, or scene note (cite note).
- **`[added]`:** Aesthetic embellishment or composition fill supplied by the AI.

---

## 2. Step-by-Step Prompt Crafting

1. **Read Character & Location Notes in Full (`inspected`):**
   Read `<Project>/02_Story_Bible/characters/<name>.md` and any associated costume/location notes. If prompting a specific scene, read the exact chapter passage.
2. **Structure the Prompt:**
   - **Subject & Features:** Face, eyes, hair, expression `[note]`
   - **Costume & Accessories:** Canonical outfit, insignia, weapons `[note]`
   - **Pose & Action:** Body language and gesture anchored to character temperament `[note]`
   - **Environment & Lighting:** Setting, color palette, atmospheric depth `[added]` / `[note]`
   - **Art Style:** Stylized, anime aesthetic, or painterly rendering aligned with project style modes (`[[m03-dark-stylized]]` or `[[p01-personal-fandom]]`).
3. **Present Prompt in Chat:**
   Return the prompt directly in conversation (do not create standalone vault notes for transient one-off prompts).
- Include `- Used: fanart-prompt` in the handoff block.
