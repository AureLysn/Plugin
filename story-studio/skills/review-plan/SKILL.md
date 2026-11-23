---
name: review-plan
description: "Audit a chapter_plan or arc outline against 7 structural, POV, hook, and pacing gates using plan_gate.py and craft rules before drafting begins. Use when reviewing an outline ('duyệt dàn ý', 'review-plan', 'kiểm tra dàn ý chương')."
---

# `review-plan` — 7-Gate Chapter Plan Audit

## 1. Purpose & Blind Audit Option

- Executed by the `xuong-kiem` subagent (or main session) **before** `write-chapter` begins.
- References: `[[scene-goal-conflict-outcome]]`, `[[scene-must-turn]]`, `[[one-point-of-view-per-scene]]`, `[[setup-and-payoff]]`, `[[05-visibility]]`.

---

## 2. The 7 Outline Gates

1. **Deterministic `plan_gate.py` check (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Utilities/plan_gate.py --project <CODE>
   ```
   The tool takes the project, not a plan: it confirms the stages before planning are in place and lists the notes a plan must have been written against. Gates 2–7 below are reading work (`inspected`) on the plan itself.
2. **POV Firewall (`[[05-visibility]]`):** Does any scene require the POV character to act on information of a secret that lists them in `unknown_to`, or in none of its three lists, in `<Project>/02_Story_Bible/secrets/`?
3. **Scene Value Turn (`[[scene-must-turn]]`):** Does every scene shift at least one narrative/emotional value (`+` ↔ `-`), or is there a static "talking heads / filler" scene?
4. **Causal Link (`[[scene-and-sequel]]`):** Are scenes connected by `"therefore"` / `"but"` rather than episodic `"and then"`?
5. **Hook Ledger Alignment (`hook_ledger.py`):** Does the plan advance or pay off the hooks it claims to touch without paying off a major hook prematurely without setup (`[[setup-and-payoff]]`)?
6. **Character Voice & Agency:** Do characters act according to their established goals/flaws in `02_Story_Bible/characters/` rather than serving as passive exposition mouthpieces (`[[exposition-through-action]]`)?
7. **Pacing & Word Budget:** Does the scene count fit the project's target chapter length in `02_Story_Bible/style/targets.md`?

---

## 3. Output Format

Report each of the 7 gates as `PASS`, `WARN`, or `FAIL` with specific scene/line references (`[[feedback]]`). If any gate is `FAIL`, block transition to `write-chapter` until revised.
- Include `- Used: review-plan` in the handoff block.
