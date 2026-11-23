---
name: crosscheck-canon
description: "Reconcile story facts against primary franchise canon in 05_Evasion/01_Oeuvre/Database/Fandom/<UNIVERSE>/ and classify divergences by canon_layer. Use when verifying canon accuracy ('đối chiếu canon', 'crosscheck-canon', 'kiểm tra nguyên tác')."
---

# `crosscheck-canon` — Franchise Canon Reconciliation

## 1. Preconditions & Precedence Ladder

- Authoritative workflow: `[[crosscheck-canon-workflow]]` (`01_Origine/04_Tools/Workflows/canon-check/crosscheck-canon-workflow.md`), `[[03-precedence]]`, `[[04-lanes]]` §2.2, `[[canon-reference-fidelity]]`.
- Remember the precedence order in `[[03-precedence]]`: within a continuation project, explicit events and rules established by the fic (`fic_explicit` / `project_locked`) override baseline franchise canon (`official_canon`), **provided the divergence is deliberate and documented**.

---

## 2. Step-by-Step Procedure

1. **Query `Database/Fandom/<UNIVERSE>/` and the project's `02_Story_Bible/`:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --query "<entity-or-rule>" --include-fiction
   ```
2. **Classify each compared fact into one of three buckets:**
   - **Aligned (`official_canon`):** The story follows the source franchise rule; link to the shared note in `05_Evasion/01_Oeuvre/Database/Fandom/<UNIVERSE>/`.
   - **Intentional Fic Divergence (`fic_explicit` / `author_confirmed`):** The fic author deliberately changed a timeline, age, or power mechanic. Record this as a `scope: project` fact in `<Project>/02_Story_Bible/world-rules/` citing the exact fic chapter (`source.ref`).
   - **Unexplained Contradiction / Question (`status: unresolved`):** If two equally authoritative sources conflict (`[[CLAUDE]]` Invariant 8), create a `type: question` note and ask Aurel to lock a decision (`type: decision`, `canon_layer: project_locked`).
3. **Verify zero project contamination in `Database/Fandom/`:**
   Run `vault_doctor.py --include-fiction` and confirm no project codes or project-scoped links were added to `Database/Fandom/`.
- Include `- Used: crosscheck-canon` in the handoff block.
