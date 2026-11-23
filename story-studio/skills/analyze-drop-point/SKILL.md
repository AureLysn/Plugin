---
name: analyze-drop-point
description: "Analyze the exact point where an unfinished source story stopped: inventory open narrative hooks, unresolved character arcs, active secrets, and timeline state. Use when preparing to continue a dropped/hiatus story ('phân tích điểm dừng', 'analyze-drop-point', 'điểm tác giả dừng')."
---

# `analyze-drop-point` — Source Drop-Point & Open Thread Audit

## 1. Preconditions & Workflow

- Authoritative workflow: `[[drop-point-analysis-workflow]]` (`01_Origine/04_Tools/Workflows/canon-check/drop-point-analysis-workflow.md`), `[[07-state]]`, `[[setup-and-payoff]]`.
- Require that at least the final `3–5` source chapters before the hiatus/drop point have been read in full (`inspected`) and recorded in the reading ledger, which is the coverage section of the source note in `01_Project-canon/sources/`.

---

## 2. Four-Step Drop-Point Audit

1. **Pinpoint the Exact Stop State (`chNN`):**
   - Record the final published chapter number, in-story date/time (`03_Development/timeline/`), physical locations of all active characters, and the immediate scene cliffhanger.
2. **Audit Open Narrative Hooks (`hook_ledger.py`):**
   - Ensure every unresolved mystery, Chekhov's gun, or promised confrontation is registered as a `type: hook` note (`status: open` or `partially_paid`) in `<Project>/03_Development/tracker/`.
   - Run:
     ```bash
     python 01_Origine/04_Tools/VaultTool/Tracking/hook_ledger.py --project <CODE>
     ```
3. **Audit Active Secrets (`02_Story_Bible/secrets/` — `[[05-visibility]]`):**
   - Verify the `known_by`, `suspected_by` and `unknown_to` lists reflect who knows what **at the exact drop point** (distinguishing `occurred` canon from author's future spoilers in comments — `[[CLAUDE]]` Invariant 7).
4. **Synthesize `<Project>/00_Overview/drop-point.md`** (the name all 14 projects use and `plan_gate.py` looks for)**:**
   - Group open threads into **Immediate (Next `1–3` Chapters)**, **Mid-Arc**, and **Endgame**, and list any open questions (`type: question`, `status: unresolved`) requiring Aurel's decision.
5. **Run `vault_index.py --build --include-fiction` and `vault_doctor.py --include-fiction`.**
- Include `- Used: analyze-drop-point` in the handoff block.
