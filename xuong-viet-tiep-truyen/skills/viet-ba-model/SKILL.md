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
2. **Brief DeepSeek.** One running chat per **two chapters** (a chat holding five chapters failed with "Check network and retry" on almost every message — PPCT arc 5). A new chat starts with the project setup (pairing, format header, rules) before the first brief. Ask for each chapter in two or three turns (blocks A–B, then the rest), never a whole chapter in one turn: answers get cut off. The brief carries: target language and length per block; labelled blocks (`【B】`, `【D】`…) so they can be spliced; the exact sentence the block follows and precedes; appearance lines copied from the vault (DeepSeek invents appearances otherwise); the bans (punctuation, banned words from `ai-tells.md`, secrets, what the room may and may not know). DeepThink on; Search on only for canon research. Every brief also carries:
   - `思考简短，不要数字数` — DeepThink otherwise counts characters in its reasoning until the turn runs out.
   - **No sample dialogue lines.** DeepSeek copies example lines verbatim into the prose (PPCT ch39). Describe what a line must do, not its words; give exact words only for lines the plan fixes.
   - **Metaphors spelled out.** "Four pieces" became four burnt fragments laid on the floor (PPCT ch38): say "four clues, not objects".
   - The weather and the day markers of the branch (e.g. "rain and frost, no snow"); characters must not say day numbers or "chapter N".
   - The branch's own earlier wording, not the `final` text, when a rewrite runs as a parallel branch: each chapter depends on the previous **branch** chapter, and the scene card keeps a "branch adjustments" table.
3. **First check (Claude).** Extract the answer, then fix before anything else:
   - appearance or facts invented from memory;
   - viewers who "remember" or "know" what they cannot (the most frequent DeepSeek error);
   - motifs repeated as emotion signals (coin stops, hands on knees, silent hugging of a sword);
   - summary lines at paragraph ends, over-explaining similes;
   - continuity with earlier chapters (names, places, timeline, light sources, counts).
   - speaker tags after the quote (DeepSeek does this even when the brief bans it) and missing `？`;
   - invented details that create canon problems (an unnamed man walked up to the church on a day nobody planned; a bag in a priest's hand);
   - scenes doubled at a block boundary (the end of block D repeated at the start of E).
   Run `ai_tells_check.py --chapter <draft> --project <CODE>` and `chapter_gate.py <draft>`. If the draft is under the project's floor, report it; add **real** content, never padding. Plan for it: in PPCT about half the first drafts were under the floor, some by 40 % (ch42: 928 against 1,500). Ask DeepSeek for one to four named passages, each with its exact insertion point and concrete content (a street on the way, a room someone looks into, a morning exchange), then splice them yourself. A construct hit can be a false positive (`“Rider”一句话不说` matched the post-quote-tag pattern): rephrase rather than argue with the gate.
4. **Review (GPT).** One ChatGPT project per story (CLS: project "CLS", *Project-only memory*). Send the brief + full chapter text the first time; for re-reviews send only the changed passages. Tell GPT the project's own rules up front so it does not flag them (e.g. CLS: Welt's cracked glasses are deliberate; describe appearance before the name). Ask for a short table: continuity, room knowing beyond evidence, voice/motifs, language, pacing, then strengths and at most six fixes ranked.
5. **Final check (Claude).** Verify each GPT point against the text and the vault. Apply the true ones; record the ones not followed and why. Re-run the checks; record numbers in `-kiem.md`. GPT is right most often about characters concluding beyond their evidence; it is wrong most often when it argues against a beat the approved plan or the canon fixes (a Servant recalled by command spell from a car; a dark seal relit by tracing). Those go in the "not followed" column with the plan line that overrides. After GPT edits, re-count: trims can push a chapter back under the floor.
6. **Parallel branch.** When the rewrite is a parallel version: never touch the `final` chapters or state files, never run `state_apply`; record the branch in `06_Alternate_Versions/branches/<branch>.md` with a progress row per arc, the chat URLs and the lessons; after each arc, confirm the old `chNN-chapter.md` files kept their modification time.

## 4. Browser mechanics (built-in browser)

- Aurel logs in to DeepSeek and ChatGPT himself; Claude never types credentials.
- Long input: `find` the textbox, then `form_input`. The built-in browser **cannot paste** from the system clipboard, and a localhost fetch from the chat page is blocked; the text has to go in through `form_input`.
- ChatGPT's editor turns newlines into spaces. After `form_input`, rebuild paragraphs by splitting on double spaces into `<p>` elements, then send.
- Waiting: poll in calls under 45 s (`await` 40 s, then read the last message's length; stop when it is stable twice). DeepSeek's answer text is the last `.ds-message`; ChatGPT's is the last `[data-message-author-role="assistant"]`.
- PowerShell variable names are case-insensitive: `$f` and `$F` are the same variable.
- **ChatGPT input that keeps paragraphs:** set the editor's `innerHTML` to one `<p>` per line through the JavaScript tool, dispatch an `InputEvent('input')`, wait a second, then click `button[aria-label=Send]` (or `[data-testid=send-button]`). Keep long chapter text in `window.__name` across two calls when one call would be too long.
- **DeepSeek after a re-login:** it may log out mid-arc; Aurel logs in again. Then check DeepThink and Search before the next brief: they flip by themselves (a 932-character chapter came back with Search on and DeepThink off). Read their state from the toggle's text colour (blue = on), and click the toggle by `find` ref.
- **"Check network and retry":** do not type the brief again into the box (that duplicates the turn). Use the pencil icon under the failed message, then its Send button. If the same chat keeps failing, open a new chat with a short context paragraph for the remaining passage.
- **Narrow pane:** when the browser pane is hidden or narrow, the page stops rendering (screenshots time out, `.ds-markdown` stays empty) and Enter does not send. Take one screenshot to force a render; send with the send button found by `read_page` (`filter: interactive`), not with Enter.
- **"Policy check temporarily unavailable"** on a browser call: do local work, then retry the same call.
- DeepSeek's latest answer is the last `.ds-markdown`; the thinking text is a separate block, so the answer count can grow by two per turn.

## 5. Model notes from the first run

- **DeepSeek:** strong at outline options and comic detail; writes short (often half the requested length); invents appearance and room memories; drifts into ordering errors on canon timelines. Always give appearance lines and the room's knowledge limits.
- **GPT:** strong beta reader; catches continuity and "room knows too much" errors Claude missed; does not know the project's own rules unless told; rates and ranks clearly.
- **Claude:** owns the vault, the canon notes and the final text. Records every Aurel answer verbatim.

**Second run — PPCT parallel branch `deepseek-20261115`, ch16–ch42 (27 chapters, 6 arcs, 15–16/11/2026):**
- DeepSeek's recurring errors, in order of frequency: speaker tags after quotes; snow in a rain-and-frost week; day numbers spoken aloud; characters knowing more than they saw; invented props and people; meta jokes ("第N章"); repeating the brief's example lines.
- GPT scores in arcs 5–6 ran 7.8–8.6 per chapter. Most of its points were applied; those not followed conflicted with the approved plan or canon.
- Budget: about 4–6 DeepSeek turns and one GPT turn per chapter, two chapters per GPT message.

## 6. Handoff

Include `- Used: viet-ba-model` and list: chapters drafted, word counts, GPT rounds, open questions for Aurel.
