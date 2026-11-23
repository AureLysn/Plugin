# Fiction Studio Working Standard (`shared/working-standard.md`)

Mandatory operating rules for every skill and subagent in **`story-studio`**.

---

## 1. Language Boundary (`[[CLAUDE]]` & `[[12-user-profile]]`)

1. **System & schema documents (`01_Origine/`):** English.
2. **Conversation with Aurel:** Vietnamese (`Mình` ↔ `Aurel` / `bạn`).
3. **Fiction project notes & chapters (`05_Evasion/01_Oeuvre/`):**
   - Prose chapters (`type: chapter`) are written in the target literary language of the project (Vietnamese or Chinese/Japanese as specified in the project's `02_Story_Bible/style/targets.md`).
   - Entity notes, outlines, and summaries inside `05_Evasion/01_Oeuvre/` preserve bilingual terms and original character/skill aliases (`aliases:`) so cross-language search (`vault_index.py --query ... -f`) resolves every name.

---

## 2. Provenance & Evidence Precedence (`[[03-precedence]]`)

1. **Every `type: fact` or canon claim requires provenance:**
   ```yaml
   canon_layer: fic_explicit   # or official_canon, author_confirmed, project_locked, etc.
   source:
     type: fic_text            # fic_text | author_comment | franchise_canon | fandom_wiki | user_input | inference
     ref: "ch12, §3 — quoted passage or event"
   authority: original_author  # original_author | franchise | fandom | user | ai
   confidence: 0.95            # authority: ai can NEVER have confidence: 1.0
   ```
2. **Distinguish `planned` from `occurred` (`[[CLAUDE]]` Invariant 7):**
   - Outlines (`type: chapter_plan`, `status: planned`) and draft chapters (`status: draft`) are **not** canon history.
   - Only events from chapters with `status: final` (`status: occurred`) update character state or pay off hooks (`[[07-state]]`).

---

## 3. Reading Ledger Law for Long Sources (`[[reading-ledger-rule]]`)

When extracting entities, tropes, or canon from a multi-chapter source:
- Maintain the reading ledger in the source note (`01_Project-canon/sources/<source>.md`, coverage section; `sources/_MOC.md` when one source spans several notes) recording exact chapter ranges read (`executed` / `inspected`), word counts, and extracted notes.
- Never claim "read all chapters" if only a sample or grep search was run.
- **Web novel sites (wikicv.org, convert sites and similar):** read one chapter at a time with a pause between pages. Open the table of contents, then only the chapters needed; to search by keyword, ask Aurel which chapters first. Never fetch dozens of chapters in a row from the browser: on 2026-11-17 a scan of about 70 parts got Aurel's own IP blocked by wikicv.org (Cloudflare 1006). These sites block bots, and the block falls on Aurel's IP. *(Moved here from session memory on 2026-11-23, Aurel: story rules load only for story work.)*

---

## 4. Two-Gate Fiction Writing Protocol (`[[session-handbook]]` & `[[09-gates]]`)

1. **Gate 1 — Pre-Drafting (`plan_gate.py` + Aurel Approval):**
   - Run `plan_gate.py --project <CODE>` before outlining (the earlier stages are in place), complete the `chapter_plan` (`type: chapter_plan`), dispatch `xuong-kiem` (`review-plan`), and **wait for Aurel to approve the outline** before writing chapter prose (`write-chapter`).
2. **Gate 2 — Pre-Finalization (`chapter_gate.py` + `xuong-kiem` + Aurel Sign-off):**
   - Run `chapter_gate.py <chapter.md>` (`style_metrics`, `ai_tells_check`, `pov_leak_check`) and dispatch `xuong-kiem` (`check-continuity`, `check-style`). The main session writes the findings and the fixes into `ch<NN>-review.md` beside the chapter; `state_apply.py` refuses to apply without it.
   - Promote `status: draft` → `status: final` and apply `state_apply.py` **only** after all gates pass (`exit 0`) and Aurel approves the chapter.
3. **One exception to "Aurel approves" (Aurel, 2026-10-25), inside a queue only:** when a project's queue has `config.auto_approve` on, `giao_viec.py auto` may approve the plan stop and the commit stop of a chapter by itself — only if the review and fix steps reported 0 serious findings and the measured gate passed (`plan_gate` for the plan; a clean `state_apply` dry run that touches no secret for the commit). Every such approval is listed for Aurel to look at afterwards (`seen`). The arc gate, and anything outside a queue, always waits for Aurel.
