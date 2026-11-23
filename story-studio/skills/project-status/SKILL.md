---
name: project-status
description: "Inspect where a fiction project stands and determine the single next actionable step (resolving blocking questions, reviewing drafts, outlining, or writing). Use when opening a project or resuming work ('đang làm đến đâu', 'tiếp theo làm gì', 'trạng thái project', 'where am I', 'project-status')."
---

# `project-status` — Project Health & Next Step Navigator

## 1. Role & Purpose

Answers the question: **What happens next on this project?**
- Identifies the next actionable step in priority order:
  1. Blocking unresolved question (`type: question`, `status: unresolved`)
  2. Finished chapter draft awaiting verification/review
  3. Approved chapter plan ready for prose drafting
  4. Outline planning for the next chapter or arc

---

## 2. Step-by-Step Status Check

1. **Run `project_table.py` (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Reporting/project_table.py
   ```
2. **Inspect Project Health via `vault_doctor.py` (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction --zone 05_Evasion/01_Oeuvre/Studio/<Branch>/[CODE]
   ```
3. **Audit Active Hooks & Open Questions (`Tracking/hook_ledger.py`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/hook_ledger.py --project <CODE>
   ```
4. **Determine the Single Next Step:**
   Based on `origin:` (`continuation` vs `original`):
   - `continuation`: `ingest-sources` → `extract-entities` → `analyze-style` / `analyze-drop-point` → `plan-continuation` → `write-chapter` → `finalize-chapter`.
   - `original`: `brainstorm-premise` → `worldbuild-original` → `plan-continuation` → `write-chapter` → `finalize-chapter`.
5. **Output a Concise 5-Line Status Summary in Vietnamese:**
   - Current stage & chapter count
   - Next actionable step with recommended skill
   - Open blocking questions or overdue hooks
   - Doctor status (`exit 0/1/2`)
- Include `- Used: project-status` in the handoff block.
