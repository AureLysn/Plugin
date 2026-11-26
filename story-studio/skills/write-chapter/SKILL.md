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
2. **Draft `<Project>/04_Manuscript/chapters/<arc>/ch<NN>/ch<NN>-chapter.md` (`type: chapter`, `status: draft`, `pov:` = the ids of the viewpoint characters, as the secrets of the project name them; with more than one, and break lines between the scenes, also `scene_povs:` = one id per scene in the order of the text):**
   Enforce the core prose rules from `01_Origine/02_Knowledge/Curated_Notes/writing/`:
   - **Strict 1 POV per scene (`[[one-point-of-view-per-scene]]`):** Zero head-hopping; never describe what the POV character cannot perceive or know (`[[05-visibility]]`). A change of POV is a new scene: put the project's break line between them (a line of symbols only, such as `＊＊＊`, `---` or `……`). Where the project's hard rules allow no break lines, leave `scene_povs` out: the gate cannot place the scenes and lists the lines to read instead.
   - **Cut redundant explanation (`[[resist-the-urge-to-explain]]` · `[[show-and-tell-balance]]`):** When an action or dialogue line already conveys the emotion, do **not** append an explanatory clause (*"bởi vì..."*, *"điều đó chứng tỏ..."*).
   - **Action beats over speech-tag chains (`[[said-and-action-beats]]`):** Keep speech tags (`nói`, `hỏi`, `đáp`, `道`, `说`) `≤ 35%` of dialogue lines; anchor the rest with physical action beats or zero-tag turn-taking.
   - **Sentence rhythm (`[[vary-sentence-length]]`):** Match the project's measured sentence-length envelope in `02_Story_Bible/style/targets.md`.
3. **Run `chapter_gate.py` immediately after writing (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Validation/chapter_gate.py <path-to-chNN-chapter.md>
   ```
   Exit `2` is a hard rule: an em dash, an ASCII ellipsis, a banned phrase, a phrase repeated from other chapters (checked only with `--corpus <flat folder of chapters>`), a forbidden character or construct of `ai-tells.md` (`ai_tells_check`), a secret the POV may not know (`pov_leak_check`), a chapter without a readable `pov` in a project with secrets, a rule of the project that cannot be read, or **broken output** (`degeneration.py`, 0.19.0): the text stops in the middle of a sentence, a paragraph or scene stands twice, a placeholder, a refusal or an assistant's remark, a scene-card field, a label of the pipeline, characters of another script, under half of the length floor. Exit `1` is a style target that was missed (the length floor of the `gate:` block, or of `targets.md` where the project has none), an AI-tell warning, a large part of the file outside the story, or a POV place to read: in a chapter with several POVs and no `scene_povs` that fits its scenes, the gate lists the lines where a secret stands that one POV may know and another may not; declare the POV of each scene and run it again. Revise the named lines (`--full` prints every place, the em dashes and ASCII ellipses by line) and re-run until `exit 0`, or until what is left is only for Aurel to decide; regenerate a broken passage instead of patching around it. Since 0.20.0 the gate runs `style_metrics`, `ai_tells_check` and `pov_leak_check` itself; do not run them beside it. Its STYLE part also prints the dialogue, paragraph and sentence figures that no tool judges: compare them with `targets.md`.
   A POV finding is settled in the text. If the POV has learned the secret, if a `leak_terms` word is too general, or if this is the planned reveal (`reveal_planned`), the secret note has to change: ask Aurel.
   A broken-output finding that is intended (a word in another script, an ending without a full stop) is waived only by Aurel, in the project's `ai-tells.md`: `gate.degeneration_ok`, one item per waiver (`code` or `code: words of the line`), with the date as a comment. The gate keeps printing what it waived.
   The gate also exits `2`, before reading the chapter, when the project's `02_Story_Bible/style/ai-tells.md` has no full `gate:` block (the measured baseline of the author being continued). That is not a defect of the chapter: an original story (`origin: original` in the project note) needs no block and no flag; a project note without `origin:` takes `--allow-no-gate`; for a continuation, the baseline must be measured first (`analyze-style`), or Aurel waives the gate for the project (in a queue: `config.waived_gates`, with the reason). Do not report Gate 2 as passed in either case without saying which.
4. **Rebuild index and run `vault_doctor.py --include-fiction`.**
- Include `- Used: write-chapter` in the handoff block.
