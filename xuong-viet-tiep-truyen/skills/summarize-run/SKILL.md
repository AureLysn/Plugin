---
name: summarize-run
description: "Synthesize findings across multi-worker extraction or drafting passes into a single structured report with seam checks, leaving worker files unedited. Use when compiling multi-agent or batch extraction results ('tổng kết cho mình', 'tổng hợp kết quả trích xuất', 'summarize-run')."
---

# `summarize-run` — Multi-Worker Batch Synthesis & Seam Check

## 1. Role & Honesty Invariant

- Executed by `xuong-lam` (or main session) after a multi-batch extraction or drafting run.
- **Role:** You **fix nothing** directly. A defect in an extracted entity or scene goes back to its originating step; a disputed canon interpretation goes to Aurel.

---

## 2. Synthesis Procedure

1. **Read All Worker Outputs in Full (`inspected`):**
   Read in narrative order, not the order tasks finished.
2. **Inspect Seams Between Segments (`inspected`):**
   Verify where Unit A ends and Unit B begins:
   - Identical in-story time of day, location, and character presence
   - Consistent forms of address (`addressing`)
   - Zero fact contradictions between segments
   - Quote both sides of any seam discrepancy.
3. **Collate Reviewer Findings:**
   Combine findings from `check-continuity` and `check-style` without softening severity rankings.
4. **Produce Summary Note:**
   Write `<Project>/00_Overview/<unit>-tong-ket.md` (`type: info`, `lane: personal`, `status: review`) with sections:
   - Parts completed (worker, file, word/note counts)
   - Findings by severity (`High` / `Medium` / `Low`)
   - Seam continuity verification
   - Decisions required from Aurel
- Include `- Used: summarize-run` in the handoff block.
