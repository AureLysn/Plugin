---
name: analyze-style
description: "Measure and codify an original author's prose style into the project's 02_Story_Bible/style/ notes (targets.md, signature.md, ai-tells.md) using style_metrics.py and qualitative voice analysis. Use when profiling a story's prose style ('phân tích văn phong', 'đo style', 'analyze-style')."
---

# `analyze-style` — Quantitative & Qualitative Style Profiling

## 1. Preconditions & Principle (`[[rule-is-a-hypothesis]]`)

- Read `shared/vault-config.md`, `[[style-audit-workflow]]`, and the writing craft rules in `01_Origine/02_Knowledge/Curated_Notes/writing/` (`[[vary-sentence-length]]`, `[[said-and-action-beats]]`, `[[show-and-tell-balance]]`).
- **Core Rule (`[[rule-is-a-hypothesis]]`):** Every numeric style target (`sentence_mean`, `dialogue_ratio`, `short_sentence_pct`) must be **measured from the real source chapters** using `style_metrics.py`, never invented from generic rules of thumb.

---

## 2. Step-by-Step Procedure

1. **Run `style_metrics.py` across representative source chapters (`executed`):**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Reporting/style_metrics.py <source-files-or-folder>
   ```
   Record the measured baseline distribution (`p10–p90`) for:
   - Word/unit count per chapter (`script: latin` vs `script: cjk`)
   - Sentence length mean & standard deviation
   - Short sentence ratio and dialogue line ratio
2. **Perform qualitative voice & rhythm analysis (`inspected`):**
   Inspect `3–5` pivotal chapters (opening, high-tension conflict, quiet character beat) to identify:
   - Narrative distance and free indirect discourse habits
   - Sensory grounding patterns (`[[concrete-specific-detail]]`)
   - Dialogue tag vs action beat ratio (`[[said-and-action-beats]]`)
   - Recurring structural framing (e.g., `go—>` / author notes in Chinese webnovels — `[[chinese-webnovel-chapter-conventions]]`)
3. **Write or update the notes in `<Project>/02_Story_Bible/style/`:**
   - `02_Story_Bible/style/targets.md` (`type: style`, `strength: target`) — machine-readable metric envelopes.
   - `02_Story_Bible/style/signature.md` (`type: style`, `strength: target`) — diction, POV filter, and dialogue rules with verbatim examples from the source.
   - `02_Story_Bible/style/ai-tells.md` (`type: rule`, `strength: hard`) — forbidden AI clichés and `gate:` regex ceilings verified by `ai_tells_check.py`.
4. **Verify with `vault_doctor.py --include-fiction` and `chapter_gate.py`.**
- Include `- Used: analyze-style` in the handoff block.
