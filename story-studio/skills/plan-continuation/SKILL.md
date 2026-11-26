---
name: plan-continuation
description: "Create a multi-chapter arc outline (type: arc) or a 7-gate chapter outline (type: chapter_plan) with scene cards and verify it via plan_gate.py. Use when outlining upcoming chapters ('lập dàn ý', 'plan-continuation', 'lên khung chương')."
---

# `plan-continuation` — Arc & 7-Gate Chapter Outlining

## 1. Preconditions & Craft Rules

- Read `shared/vault-config.md`, `shared/working-standard.md`, `[[05-visibility]]`, `[[07-state]]`, and the structure/scene rules in `01_Origine/02_Knowledge/Curated_Notes/writing/`:
  - `[[scene-goal-conflict-outcome]]`, `[[scene-and-sequel]]`, `[[scene-must-turn]]`, `[[setup-and-payoff]]`, `[[chapter-end-hook]]`, `[[one-point-of-view-per-scene]]`.
- **Two-Gate Protocol (`[[session-handbook]]`):** Never write full chapter prose (`write-chapter`) in the same step as creating the outline. Stop after Gate 1 (`review-plan`) so Aurel can review and approve the outline.

---

## 2. Step-by-Step Procedure

1. **Confirm the project is ready to be planned (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Utilities/plan_gate.py --project <CODE>
   ```
   `plan_gate.py` takes the project only. It checks that the stages before planning left their notes (sources, entities, `00_Overview/drop-point.md`, `02_Story_Bible/style/targets.md`, canon links, `03_Development/structure/tropes.md`, and for an original story `03_Development/structure/premise/premise.md`) and prints what must be read before outlining. Exit `2` = a stage is missing: go back to it.
2. **Resolve Permitted Context & Active Hooks:**
   Run from `D:\AureLysn`:
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/context_resolver.py --project <CODE> --pov <character-slug> --role planner
   python 01_Origine/04_Tools/VaultTool/Tracking/hook_ledger.py --project <CODE>
   ```
3. **Draft `<Project>/04_Manuscript/chapters/<arc>/ch<NN>/ch<NN>-plan.md` (`type: chapter_plan`, `status: planned`):**
   Use `01_Origine/04_Tools/Templates/writing/Chapter-Plan.md` and `Scene-Card.md`. Every scene must explicitly state:
   - **Single POV character** (`[[one-point-of-view-per-scene]]`; `pov:` of the card, cards named in the order of the scenes: `scenes/01-…`, `02-…` in the chapter's folder — the gate checks each scene by its card) and what secrets they are **forbidden** to know (`unknown_to` in `02_Story_Bible/secrets/`). What the scene must not touch stands in the card's `forbidden_secrets:`, what the whole chapter must not touch in the plan's (`[[05-visibility]]` §4).
   - **Goal → Opposition → Outcome** (`Yes, but` / `No, and furthermore` — `[[scene-goal-conflict-outcome]]`).
   - **Value Shift (`+/-`)** (`[[scene-must-turn]]`) — if a scene starts and ends on the same emotional/narrative value, cut or merge it.
   - **Hooks planted / advanced / paid off** (`03_Development/tracker/`) and the **chapter-end hook** (`[[chapter-end-hook]]`).
4. **Check the plan note itself (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   ```
   Fix any missing fields or broken links. The plan's content (POV, value turn, hooks) is judged by `review-plan`; scripts read only its `forbidden_secrets`, through `chapter_gate`, when it sits beside the chapter ([[05-visibility]] §4).
- Include `- Used: plan-continuation` in the handoff block.
