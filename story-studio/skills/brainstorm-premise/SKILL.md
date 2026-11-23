---
name: brainstorm-premise
description: "Develop a raw idea, image, or creative spark into a validated premise for an original-fiction project (origin: original) before worldbuilding begins. Use when exploring a new original story idea ('tôi có một ý tưởng', 'brainstorm cốt truyện', 'brainstorm-premise', 'phát triển ý tưởng thành truyện')."
---

# `brainstorm-premise` — Original Story Premise Brainstorming

## 1. Role: The Creative Spark

Sits before both worldbuilding and planning.
- **`ingest-sources`** imports an existing text.
- **`plan-continuation`** plans chapters against an existing world.
- **`brainstorm-premise`** turns a raw idea into a stable foundation for `worldbuild-original`.

---

## 2. Step-by-Step Procedure

1. **Capture the Spark Verbatim First (`<Project>/03_Development/structure/premise/spark.md`):**
   Record Aurel's original words without polishing. Early polishing risks losing what made the idea appealing.
2. **Clarify Undetermined Variables:**
   Ask only what is essential:
   - Central dramatic question / thematic core
   - Target format & scope (oneshot, novella, multi-arc novel)
   - POV structure (single first-person, third limited, multiple POV)
3. **Offer 2–3 Distinct Creative Directions:**
   Present a table of alternatives (Logline, Central Conflict, Tone Anchors, Scope, and Trade-offs).
4. **Formalize `<Project>/03_Development/structure/premise/premise.md`** (the path `plan_gate.py` checks before any planning)**:**
   Once Aurel selects a direction, write `premise.md` distinguishing:
   - **Fixed Elements:** Explicitly chosen by Aurel (`canon_layer: user_canon`, `authority: user`).
   - **Open Elements / Questions:** Undecided mechanics or subplots, registered as `type: question` notes in `<Project>/05_Management/questions/`.
5. **Suggest `worldbuild-original` next (do not run it automatically).**
- Include `- Used: brainstorm-premise` in the handoff block.
