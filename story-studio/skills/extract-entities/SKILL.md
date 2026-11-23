---
name: extract-entities
description: "Extract characters, locations, organizations, facts, secrets, hooks, and timeline events from source chapters into the project's 02_Story_Bible/ and 03_Development/ folders or Database/Fandom/. Use when extracting story entities from source text ('trích xuất thực thể', 'extract-entities', 'lập hồ sơ nhân vật từ nguồn')."
---

# `extract-entities` — Source Entity & Canon Fact Extraction

## 1. Preconditions & Dispatch Threshold (`[[13-agent-routing]]`)

- Read `shared/vault-config.md`, `shared/working-standard.md`, `[[02-entity-types]]`, `[[03-precedence]]`, `[[04-lanes]]`, `[[05-visibility]]`, and `[[reading-ledger-rule]]`.
- **Subagent threshold:** If the source batch exceeds **`~15,000` words** (or `≥ 10` files), propose model/effort to Aurel and dispatch the `xuong-lam` agent on bounded chapter batches (`3–5` chapters per run) so raw source text does not flood the main session.

---

## 2. Scope Routing (`Database/Fandom/` vs the project's `02_Story_Bible/` and `03_Development/`)

Before creating or updating a note, classify its `scope` (`[[04-lanes]]` §2.2):
1. **Unaltered franchise canon (`scope: universe`):**
   - Place in `05_Evasion/01_Oeuvre/Database/Fandom/<UNIVERSE>/` (`canon_layer: official_canon` or `fandom_wiki`).
   - **Never** include project codes (`PPCT`, `EMB`, etc.) or fic-specific plot changes in `Database/Fandom/`.
2. **Story-specific state, OC, or canon divergence (`scope: project`):**
   - Place in the project's `02_Story_Bible/` or `03_Development/` folder for its type, as §3 lists (`project: <CODE>`, `canon_layer: fic_explicit` or `project_locked`). `01_Project-canon/` holds source notes only.

---

## 3. Extraction Procedure

1. **Read the assigned source chapters in full (`inspected`):**
   Never extract from grep snippets alone. Record every chapter read in the reading ledger: the coverage section of the source note in `<Project>/01_Project-canon/sources/`.
2. **Create or update entity notes using `01_Origine/04_Tools/Templates/`:**
   - `02_Story_Bible/characters/` (`type: character`) — include all CJK, Romaji, and Vietnamese names in `aliases:`.
   - `02_Story_Bible/secrets/` (`type: secret`) — populate `known_by: [...]`, `suspected_by: [...]`, `unknown_to: [...]` and, where a word would give the secret away, `leak_terms: [...]` (`[[05-visibility]]`).
   - `03_Development/tracker/` (`type: hook`) — populate `status: open` | `partially_paid` | `paid_off` and `introduced.chapter: chNN` (the field `Hook-Note.md` and `hook_ledger.py` use).
   - `02_Story_Bible/world-rules/` (`type: fact`) — include `subject`, `predicate`, `object` (`[[08-impact]]`) and `source.ref` with chapter + quote.
3. **Run verification gates:** `entity_check.py` asks what this section asks (a secret lists who knows it, a hook has a status and `introduced.chapter`, a fact has `source.ref` and its triple, every note carries the project code). Exit `2` = fix before handing over. It does not judge whether a note is true to the source; that is the reading recorded in the ledger.
   ```bash
   python 01_Origine/04_Tools/VaultTool/Validation/entity_check.py --project <CODE>
   python 01_Origine/04_Tools/VaultTool/Core/vault_index.py --build --include-fiction
   python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction
   ```
- Include `- Used: extract-entities` in the handoff block.
