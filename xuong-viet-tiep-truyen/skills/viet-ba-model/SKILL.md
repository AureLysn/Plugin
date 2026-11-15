---
name: viet-ba-model
description: "Three-model chapter pipeline chosen by Aurel (2026-11-15): Claude plans (outline, scene card, context pack), DeepSeek writes the prose, GPT reviews as beta reader, Claude does the final check and edit. Driven through the built-in browser on Aurel's logged-in DeepSeek and ChatGPT sessions. Use when writing or revising chapters with external models ('viết ba model', 'deepseek viết gpt kiểm', 'quy trình ba model', 'viet-ba-model')."
---

# `viet-ba-model` — Claude plans · DeepSeek writes · GPT reviews · Claude checks last

Decision: Aurel 2026-11-15, *"claude lên kế hoạch deepseek viết chính, gpt kiểm tra và claude kiểm tra lại lần cuối"*. First run: CLS arc 1 v6, ch1–ch4. The project record of the decision is `05_Evasion/01_Oeuvre/Studio/Continue/CLS_crossover-va-lenh-su/01_Project-canon/sources/user-input/20261115-quy-trinh-ba-model.md`.

## 1. Roles and gates

| Step | Who | Output | Gate |
|---|---|---|---|
| 1. Plan | **Claude** | arc outline or chapter scene card (`type: scene`), context pack | Aurel approves the outline before any prose |
| 2. Write | **DeepSeek** | prose blocks, in the target language | — |
| 3. First check | **Claude** | edited draft + error table | `ai_tells_check`, length floor, read against hard rules |
| 4. Review | **GPT** | beta-reader report | — |
| 5. Final check | **Claude** | applies only the points it verified true; logs the rest as "not followed" with the rule that overrides | `ai_tells_check`, `vault_doctor` |
| 6. Approve | **Aurel** | — | draft stays `status: draft` until Aurel approves; `final` chapters are never overwritten |

Claude never pastes a model's claim about canon as fact: everything from DeepSeek or GPT is `[DS]` / `[GPT]` and canon claims are `[cần tra]` until checked against game text or the project's canon notes.

## 2. Files (one folder per rewrite pass)

`<Project>/04_Manuscript/chapters/<arc>/chNN/rewrite-<YYYYMMDD>/`:
- `chNN-vX-the-canh.md` (`type: scene`) — block table: block id, who writes it (DeepSeek / Claude adapts from the old final), content, what the block must achieve; voices; bans.
- `chNN-vX-nhap.md` (`type: chapter`, `status: draft`) — the assembled draft; `source.ref` names the chat URL.
- `chNN-vX-kiem.md` (`type: note`) — block-by-author table, error table (DS text → fix), GPT points with Claude's verdict, numbers.

Arc-level planning and GPT reports go in `<Project>/03_Development/arcs/rewrite-<YYYYMMDD>/`. Aurel's answers go verbatim into `01_Project-canon/sources/user-input/`.

## 3. Step by step

1. **Plan (Claude).** Read the approved outline, the previous chapter's end, `02_Story_Bible/style/hard-rules.md` and `ai-tells.md`. Write the scene card. Mark which blocks DeepSeek writes and which canon blocks Claude adapts from the old `final` text (adapt, do not retype from memory).
2. **Brief DeepSeek.** One running chat per arc (keeps context). The brief carries: target language and length per block; labelled blocks (`【B】`, `【D】`…) so they can be spliced; the exact sentence the block follows and precedes; appearance lines copied from the vault (DeepSeek invents appearances otherwise); the bans (punctuation, banned words from `ai-tells.md`, secrets, what the room may and may not know). DeepThink on; Search on only for canon research.
3. **First check (Claude).** Extract the answer, then fix before anything else:
   - appearance or facts invented from memory;
   - viewers who "remember" or "know" what they cannot (the most frequent DeepSeek error);
   - motifs repeated as emotion signals (coin stops, hands on knees, silent hugging of a sword);
   - summary lines at paragraph ends, over-explaining similes;
   - continuity with earlier chapters (names, places, timeline, light sources, counts).
   Run `ai_tells_check.py --chapter <draft> --project <CODE>`. If the draft is under the project's floor, report it; add **real** content (ask DeepSeek for a further block, or adapt a canon scene), never padding.
4. **Review (GPT).** One ChatGPT project per story (CLS: project "CLS", *Project-only memory*). Send the brief + full chapter text the first time; for re-reviews send only the changed passages. Tell GPT the project's own rules up front so it does not flag them (e.g. CLS: Welt's cracked glasses are deliberate; describe appearance before the name). Ask for a short table: continuity, room knowing beyond evidence, voice/motifs, language, pacing, then strengths and at most six fixes ranked.
5. **Final check (Claude).** Verify each GPT point against the text and the vault. Apply the true ones; record the ones not followed and why. Re-run the checks; record numbers in `-kiem.md`.

## 4. Browser mechanics (built-in browser)

- Aurel logs in to DeepSeek and ChatGPT himself; Claude never types credentials.
- Long input: `find` the textbox, then `form_input`. The built-in browser **cannot paste** from the system clipboard, and a localhost fetch from the chat page is blocked; the text has to go in through `form_input`.
- ChatGPT's editor turns newlines into spaces. After `form_input`, rebuild paragraphs by splitting on double spaces into `<p>` elements, then send.
- Waiting: poll in calls under 45 s (`await` 40 s, then read the last message's length; stop when it is stable twice). DeepSeek's answer text is the last `.ds-message`; ChatGPT's is the last `[data-message-author-role="assistant"]`.
- PowerShell variable names are case-insensitive: `$f` and `$F` are the same variable.

## 5. Model notes from the first run

- **DeepSeek:** strong at outline options and comic detail; writes short (often half the requested length); invents appearance and room memories; drifts into ordering errors on canon timelines. Always give appearance lines and the room's knowledge limits.
- **GPT:** strong beta reader; catches continuity and "room knows too much" errors Claude missed; does not know the project's own rules unless told; rates and ranks clearly.
- **Claude:** owns the vault, the canon notes and the final text. Records every Aurel answer verbatim.

## 6. Handoff

Include `- Used: viet-ba-model` and list: chapters drafted, word counts, GPT rounds, open questions for Aurel.
