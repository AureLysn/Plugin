---
name: watch-frame-contract
description: "Define the rules, screening playlist, and secret-reveal tracking for a 'watching' or reaction framing device (xem ảnh thể / 观影体). Use when setting up a reaction story frame ('xem ảnh thể', 'watch-frame-contract', 'phòng xem phim', 'reaction fic', 'watching fic')."
---

# `watch-frame-contract` — Reaction & Watching Frame Governance

## 1. Genre Conventions & The "Gượng" (尬) Warning

"Watching" stories (*xem ảnh thể* / 观影体) gather characters to react to footage of their own past, future, or alternate realities.
- **The Core Pacing Trap:** When reaction beats outpace new narrative information, the story feels repetitive and shallow (*"gượng / 尬"*).
- **Two Legitimate Stances (`stance:`):**
  - `reaction_only` — pure character reactions with no plot progression outside the screening room.
  - `plot_driven` — the screening actively advances relationships, shifts character decisions, and changes the future.
  - Settle `stance:` explicitly before writing Chapter 1 so reviewers know what standard applies.

---

## 2. Five Mandatory Room Rules

Draft `<Project>/05_Management/contracts/watch-frame.md` (`id: rule.<CODE>.watch-frame`, `type: rule`, `strength: hard`, `scope: project`, `always_load: true`):

1. **`participants:`** List of characters present in the room. (If mixed-fandom, run `crossover-contract` first.)
2. **`mechanism:`** The framing device (god-like system, magical artifact, spatial anomaly) and whether it will ever be explained.
3. **`memory_retained:`** `true` by default — if characters forget what they watched upon exit, reactions lose lasting weight.
4. **`time_flow:`** Can participants pause, rewind, or skip footage?
5. **`intervention_allowed:`** `false` by default — if room occupants can reach through the screen to alter events, the story is time-travel, not reaction.

---

## 3. Every Clip Is a Secret Reveal (`finalize-chapter`)

- Never write generic *"they watch everything"* notes. Maintain a curated screening playlist of specific scenes.
- Every clip shown that reveals unknown facts to a participant must be mapped to a `known_by` / `suspected_by` transition on the corresponding note in `<Project>/02_Story_Bible/secrets/` and committed during `finalize-chapter`.
- Include `- Used: watch-frame-contract` in the handoff block.
