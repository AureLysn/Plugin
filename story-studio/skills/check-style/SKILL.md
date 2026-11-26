---
name: check-style
description: "Audit chapter prose against project style targets (02_Story_Bible/style/targets.md, signature.md, ai-tells.md) using style_metrics.py and qualitative voice rules. Use when checking prose rhythm and voice ('kiểm tra văn phong', 'check-style', 'chương này có đúng giọng văn không', 'đo nhịp câu')."
---

# `check-style` — Prose Style, Rhythm & Voice Audit

## 1. Preconditions & Style Profile

- Read `shared/vault-config.md`, `shared/working-standard.md`, and the target project's `02_Story_Bible/style/` notes:
  - `02_Story_Bible/style/targets.md` (`type: style`, `strength: target`)
  - `02_Story_Bible/style/signature.md` (`type: style`, `strength: target`)
  - `02_Story_Bible/style/ai-tells.md` (`type: rule`, `strength: hard`)
- If the project lacks a `02_Story_Bible/style/` profile, stop and route to `analyze-style`.

---

## 2. Three Audit Strengths (`[[rule-protocol]]`)

| Strength | On deviation | Action required |
|---|---|---|
| **`hard`** | Defect | **Must be fixed** before finalization (e.g., forbidden AI clichés, explicit POV leak) |
| **`target`** | Numerical miss | **Report the number and ask Aurel** (`[[CLAUDE]]` §2). Never pad prose with fluff to force a number into range |
| **`tendency`** | Stylistic preference | Note it; deliberate deviation for narrative impact is permitted |

---

## 3. Step-by-Step Audit Procedure

1. **Run `style_metrics.py` from the vault root (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Reporting/style_metrics.py <path-to-chapter.md> --project <CODE> --json
   ```
   The tool compares length and term density with `02_Story_Bible/style/targets.md`, and the em dash ban with `hard-rules.md`, by itself (`verdict`). A length it cannot read, two chapter lengths that disagree, or a term list without a threshold is exit `1`, and the JSON names the reason (`unchecked`, `length_conflict`, `density_unread`, `ket`). Compare the rest by hand:
   - Word / character count per chapter (`word_count`, `cjk_char_count`)
   - Sentences: `sentence_median`, `sentence_mean`, `sentence_ge35_ratio`, `sentence_le4_ratio` (Latin); `cjk_sentence_median`, `cjk_sentence_ge50_ratio`, `cjk_sentence_le4_per_1000` (Chinese)
   - Dialogue and paragraphs: `dialogue_paragraph_ratio` (`cjk_dialogue_ratio` for Chinese), `paragraph_mean`, `paragraph_median`
2. **Run `ai_tells_check.py` (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Validation/ai_tells_check.py --project <CODE> --chapter <path-to-chapter.md>
   ```
   Confirm zero hard matches for forbidden AI-tell regex patterns (`02_Story_Bible/style/ai-tells.md`); the tool prints the passages with their lines (`--full`: all of them). `chapter_gate.py` runs both tools too.
3. **Qualitative Voice & Craft Inspection (`inspected`):**
   Evaluate against general craft rules in `01_Origine/02_Knowledge/Curated_Notes/writing/`:
   - Dialogue punctuation & address forms (`addressing:` in relationship notes)
   - Action beats vs speech tags (`[[said-and-action-beats]]` — keep speech tags `≤ 35%`)
   - Cut closing moral summaries or unearned emotional tags (`[[resist-the-urge-to-explain]]`)
4. **Report findings with their words:**
   Present the measured table (`Rule · Target · Measured · Verdict`). Everything that points at a passage goes into one JSON block (`shared/working-standard.md` §5; categories `style`, `voice`, `dialogue`, `language`, `pacing`, `repetition`), checked with `finding_check.py`. As `xuong-kiem`, return both in the handoff; the main session checks the block again and records them in `ch<NN>-review.md` beside the chapter (needed by `finalize-chapter`).
- Include `- Used: check-style` in the handoff block.
