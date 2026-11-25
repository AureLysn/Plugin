---
name: check-continuity
description: "Audit a chapter draft or outline for continuity errors, POV secret leaks (pov_leak_check.py), timeline/countdown slips, and spatial/injury inconsistencies. Use when verifying chapter continuity ('kiểm tra mạch truyện', 'check-continuity', 'kiểm rò rỉ POV')."
---

# `check-continuity` — Continuity, Timeline & POV Leak Audit

## 1. Preconditions & Workflow

- Authoritative workflow: `[[continuity-check-workflow]]` (`01_Origine/04_Tools/Workflows/writing/continuity-check-workflow.md`), `[[05-visibility]]`, `[[07-state]]`.
- Designed to be executed by the read-only `xuong-kiem` subagent (`[[13-agent-routing]]` §2.4) or as a pre-finalization check.

---

## 2. Step-by-Step Audit Procedure

1. **Run Deterministic POV Leak & Hook Gates (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Validation/pov_leak_check.py --project <CODE> --chapter <chapter-path>
   python 01_Origine/04_Tools/VaultTool/Tracking/hook_ledger.py --project <CODE>
   ```
2. **Inspect Semantic Continuity Across 5 Axes (`inspected`):**
   Cross-read the chapter against `<Project>/02_Story_Bible/`, `<Project>/03_Development/` and the preceding chapter summary (`04_Manuscript/chapters/`):
   - **Epistemic / POV Firewall (`[[05-visibility]]`):** Does the POV character react to, infer, or use terminology belonging to a secret they have not yet learned (even without using the exact keyword banned in `pov_leak_check.py`)?
   - **Timeline & Countdowns (`03_Development/timeline/`):** Do day/night transitions, travel times, ages, and ticking clocks match prior `occurred` events?
   - **Physical State & Inventory:** Are injuries, exhaustion, clothing, weapons, and spatial positions consistent from scene start to scene end?
   - **Character Relationships (`02_Story_Bible/relationships/`):** Do forms of address (pronouns/honorifics in Vietnamese/CJK) match the current relationship stage?
   - **Branch Isolation (`[[04-lanes]]` §2.3):** If on `branch: main`, confirm zero facts from alternate `06_Alternate_Versions/branches/` leaked in.
3. **Report Findings with Their Words (`shared/working-standard.md` §5):**
   One JSON block: `FAIL` for a blocking continuity error, `WARN` for a smaller one, `NOTE` for polish; categories `pov`, `timeline`, `state`, `address`, `branch`, `canon`, `hook`, `missing`, `logic`, `repetition`. Quote the chapter, and quote the secret, timeline, plan or earlier chapter it contradicts in `against`. Run `finding_check.py` on the block. As `xuong-kiem`, return the block in the handoff; the main session checks it again and records the tables in `ch<NN>-review.md` beside the chapter (needed by `finalize-chapter`).
- Include `- Used: check-continuity` in the handoff block.
