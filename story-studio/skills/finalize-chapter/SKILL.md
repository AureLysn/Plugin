---
name: finalize-chapter
description: "Promote a chapter from draft to final (status: final) after Gate 2 passes and Aurel approves, generate and apply state deltas via state_apply.py, and update the search index. Use when accepting a finished chapter ('chốt chương', 'finalize-chapter', 'commit state', 'cập nhật trạng thái sau chương')."
---

# `finalize-chapter` — Chapter Finalization & World State Commit

> **Core Law (`[[07-state]]` & `[[09-gates]]`):**
> *Never update character states or pay off narrative hooks while a chapter is in draft.*
> State mutation occurs **only** when a chapter is promoted to `status: final` with explicit sign-off from Aurel.
> The authoritative sequence is `[[07-state]]` §3; the steps below carry it out and must not contradict it.

---

## 1. Preconditions Before Finalization

1. Chapter prose in `<Project>/04_Manuscript/chapters/<arc>/ch<NN>/ch<NN>-chapter.md` is complete.
2. `chapter_gate.py --full` passed clean (`exit 0`), without `--skip`; a part Aurel waived is named in `ch<NN>-review.md` with Aurel's reason, and Aurel approves that commit (`[[09-gates]]` §2). At exit `1`, each line it names (a missed target, an AI-tell warning, a POV place to read, a secret it cannot check) goes to Aurel with the review, as `[[09-gates]]` §2 (Seam 2) says; what was read and what Aurel accepts is recorded in `ch<NN>-review.md`. Exit `2` never goes further.
3. `xuong-kiem` (or main session) ran `check-continuity` and `check-style`; the **main session** ran `finding_check.py` on the returned block and wrote its tables and what was done about each finding into `ch<NN>-review.md` beside the chapter (`xuong-kiem` may not write). No proven `FAIL` is open, and every unproven finding is decided (`shared/working-standard.md` §5). `state_apply.py --apply` refuses a chapter folder without a `*review*.md`; `--exempt-review` is used only when Aurel says the review is waived.
4. **Aurel explicitly approved finalization** (or the queue did, within the limits of `shared/working-standard.md` §4).

---

## 2. Six-Step Finalization Sequence

1. **Extract Proposed Delta (`<Project>/04_Manuscript/chapters/<arc>/ch<NN>/delta.yaml`):**
   Propose state transitions with explicit chapter citations (`source.ref`):
   - Characters: status changes, injuries, location changes
   - Relationships: relationship level or address shifts
   - Hooks: `open` → `partially_paid` | `paid_off` (referencing hook IDs)
   - Secrets: `known_by` / `suspected_by` additions (`known_by_add`; a list written over several lines or as a block goes to "CAN SUA TAY": add the name by hand)
   - Timeline: event timestamp and summary
   - `state_apply` writes only secrets, hooks, arcs and questions; characters, relationships, timeline, new entities and any key under `changes:` that it does not know go to "CAN SUA TAY"
2. **Preview via `state_apply.py` (Dry Run):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/state_apply.py <path-to-chNN-delta.yaml>
   ```
   Present the printed table of changes to Aurel for confirmation.
3. **Apply State Changes:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/state_apply.py <path-to-chNN-delta.yaml> --apply --yes
   ```
4. **Update Chapter Frontmatter:**
   Update `ch<NN>-chapter.md` frontmatter:
   - `status: final`
   - `last_updated: YYYY-MM-DD`
5. **Create Chapter Summary:**
   Create `<Project>/04_Manuscript/chapters/<arc>/ch<NN>/ch<NN>-tong-ket.md` (the name the 25 existing chapter summaries carry) from `01_Origine/04_Tools/Templates/writing/Chapter-Summary-Note.md`.
6. **Rebuild Index & Run Gates:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   python 01_Origine/04_Tools/VaultTool/Reporting/project_table.py
   ```
- Include `- Used: finalize-chapter` in the handoff block.
