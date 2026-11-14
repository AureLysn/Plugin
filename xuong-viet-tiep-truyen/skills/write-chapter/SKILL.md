---
name: write-chapter
description: "Draft chapter prose (type: chapter, status: draft) from an approved chapter_plan, enforcing 1 POV per scene, project style targets, and zero AI-tell clichés, then run chapter_gate.py. Use when writing a chapter ('viết chương', 'write-chapter', 'soạn thảo chương')."
---

# `write-chapter` — Chapter Prose Drafting & Gate Verification

## 1. Preconditions (Gate 1 Must Be Green)

- Read `[[chapter-drafting-workflow]]` (`01_Origine/04_Tools/Workflows/writing/chapter-drafting-workflow.md`), `shared/working-standard.md`, and the project's `02_Story_Bible/style/targets.md`, `02_Story_Bible/style/signature.md`, and `02_Story_Bible/style/ai-tells.md`.
- **Hard Precondition:** Never start `write-chapter` unless `<Project>/04_Manuscript/chapters/<arc>/ch<NN>/ch<NN>-plan.md` exists, passed `review-plan`, and has been approved by Aurel (or by the queue's own approval, `shared/working-standard.md` §4).

---

## 2. Step-by-Step Drafting Procedure

1. **Load Permitted Context (`context_resolver.py`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Core/context_resolver.py --scene <path-to-scene-card.md>
   # no scene card: 01_Origine/04_Tools/VaultTool/Core/context_resolver.py --project <CODE> --pov <pov-slug>
   ```
   Read the previous chapter's ending (`ch<NN-1>`) to ensure seamless continuity of time, location, and emotional tone.
2. **Draft `<Project>/04_Manuscript/chapters/<arc>/ch<NN>/ch<NN>-chapter.md` (`type: chapter`, `status: draft`):**
   Enforce the core prose rules from `01_Origine/02_Knowledge/Curated_Notes/writing/`:
   - **Strict 1 POV per scene (`[[one-point-of-view-per-scene]]`):** Zero head-hopping; never describe what the POV character cannot perceive or know (`[[05-visibility]]`).
   - **Cut redundant explanation (`[[resist-the-urge-to-explain]]` · `[[show-and-tell-balance]]`):** When an action or dialogue line already conveys the emotion, do **not** append an explanatory clause (*"bởi vì..."*, *"điều đó chứng tỏ..."*).
   - **Action beats over speech-tag chains (`[[said-and-action-beats]]`):** Keep speech tags (`nói`, `hỏi`, `đáp`, `道`, `说`) `≤ 35%` of dialogue lines; anchor the rest with physical action beats or zero-tag turn-taking.
   - **Sentence rhythm (`[[vary-sentence-length]]`):** Match the project's measured sentence-length envelope in `02_Story_Bible/style/targets.md`.
3. **Run `chapter_gate.py` immediately after writing (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Validation/chapter_gate.py <path-to-chNN-chapter.md>
   ```
   If `chapter_gate.py` exits `2` (POV leak, AI-tell violation, or word count out of bounds), revise the offending lines and re-run until `exit 0`.
   The gate also exits `2`, before reading the chapter, when the project's `02_Story_Bible/style/ai-tells.md` has no full `gate:` block (the measured baseline of the author being continued). That is not a defect of the chapter: for an original story with no author to match, run `chapter_gate.py <chapter> --allow-no-gate`; for a continuation, the baseline must be measured first (`analyze-style`), or Aurel waives the gate for the project (in a queue: `config.waived_gates`, with the reason). Do not report Gate 2 as passed in either case without saying which.
4. **Rebuild index and run `vault_doctor.py --include-fiction`.**
- Include `- Used: write-chapter` in the handoff block.
