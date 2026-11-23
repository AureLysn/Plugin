---
name: check-conflicts
description: "Detect 3-way canon conflicts across subject-predicate-object fact triples, continuity branches, and canon_layer precedence ladders. Use when checking for fact contradictions ('kiểm tra mâu thuẫn', 'check-conflicts', 'xung đột dữ kiện')."
---

# `check-conflicts` — Three-Way Canon & Fact Conflict Detection

## 1. Preconditions & Specification

- Authoritative specification: `[[08-impact]]`, `[[03-precedence]]`, `[[04-lanes]]`, and `[[conflict-check-workflow]]` (`01_Origine/04_Tools/Workflows/canon-check/conflict-check-workflow.md`).

---

## 2. Three-Way Conflict Audit

1. **Subject–Predicate–Object Triple Collisions (`[[08-impact]]`):**
   - Inspect `type: fact`, `type: character`, and `type: event` notes in `<Project>/02_Story_Bible/` and `<Project>/03_Development/timeline/` (and `Database/Fandom/<UNIVERSE>/`). A fact without `subject` / `predicate` / `object` cannot be compared this way (`entity_check.py` lists them); compare those by reading.
   - Flag any pair of active notes asserting incompatible values for the same `(subject, predicate)` at the same story timestamp (without an intervening `status: superseded` transition).
2. **Precedence Resolution (`[[03-precedence]]`):**
   - If the two conflicting notes sit at **different** `(canon_layer, authority)` ranks (e.g., `project_locked` vs `official_canon`), the higher rank wins automatically; document the override in the project note.
   - If the two notes sit at the **same** `(canon_layer, authority)` rank (e.g., two `fic_explicit` chapters or two `user_canon` notes), **STOP and ask Aurel** (`[[CLAUDE]]` Invariant 8).
3. **Blast-Radius Impact Check (`[[08-impact]]`):**
   - When a fact is superseded (`status: superseded`, `superseded_by`, `superseded_at`), grep for all inbound wikilinks to that fact across the chapter plans and chapters in `04_Manuscript/chapters/` to identify affected scenes.
- Include `- Used: check-conflicts` in the handoff block.
