---
name: ban-giao
description: "End-of-session handoff procedure: measure live vault state, update session-handoff.md and open-items-dashboard.md, rebuild the search index last, and verify all gates pass. Use at the end of a session or when user says 'bàn giao', 'kết thúc phiên', 'cập nhật handoff', or 'chốt phiên'."
---

# `ban-giao` — End-of-Session Handoff Protocol

## 1. Preconditions & Target Files

- Authoritative workflow: `[[session-handoff-workflow]]` (its table is the home of this procedure; this skill adds the commands), `[[09-gates]]`, `[[CLAUDE]]` Invariants 11 & 12.
- Target files:
  - `06_Station/01_Daily_Logs/session-handoff.md` (`[[session-handoff]]`)
  - `06_Station/02_Dashboards/open-items-dashboard.md` (`[[open-items-dashboard]]`)

---

## 2. Five-Step Handoff Sequence

1. **Read current handoff and dashboard files first (`[[CLAUDE]]` Invariant 4):**
   Read `06_Station/01_Daily_Logs/session-handoff.md` and `06_Station/02_Dashboards/open-items-dashboard.md` before making edits.
2. **Update open items (`[[open-items-dashboard]]`):**
   - Mark completed items as resolved (with date and verification evidence).
   - Add any newly discovered **system** open items under the correct prefix (`KH-`, `HT-`, `TD-`/`AP-`).
   - **Project items never go on the dashboard or into `session-handoff`** (Aurel, 2026-11-23): Portfolio items go to `01_Origine/01_Identity/Portfolio_Plan/viec-mo-portfolio.md` (`PF-`); a story project's items go to `05_Management/viec-mo.md` inside that project (`TR-`, create the note if missing). They are read only when working on that project.
3. **Rewrite `[[session-handoff]]` in full, never append (`06_Station/01_Daily_Logs/session-handoff.md`):**
   - Record what was completed in the current session, which files were created/modified, measured gate statuses (`executed` / `inspected` / `assumed`), and the prioritized next steps.
   - Preserve `last_updated: YYYY-MM-DD` and original line endings (`LF`/`CRLF`).
4. **Rebuild the vault index LAST (after all `.md` edits are saved):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
   ```
5. **Run final verification gates:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --templates
   python 01_Origine/04_Tools/VaultTool/Validation/claim_check.py --no-scan
   ```

---

## 3. Handoff Summary Block

Output the final summary to Aurel in Vietnamese (keeping measured counts in prose or Markdown tables, never inside fenced runnable code blocks per `[[ai-collaboration-guide]]`) and include `- Used: ban-giao`.
