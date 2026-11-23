---
name: worldbuild-original
description: "Build the setting, characters, factions, and rules for a brand-new original-fiction project from an approved premise.md, using identical entity schemas so downstream tools run unmodified. Use when building an original story world ('dựng thế giới cho truyện gốc', 'worldbuild-original', 'tạo nhân vật cho truyện mới')."
---

# `worldbuild-original` — Original Worldbuilding & Entity Creation

## 1. Creative Stance vs Archivist Stance

- **`extract-entities`** is an archivist: it extracts existing text and refuses to invent.
- **`worldbuild-original`** is creative synthesis: inventing **is** the job, but **nothing is locked until Aurel approves** (`[[CLAUDE]]` §2).
- **Schema Compatibility:** Produces identical note types and folders as `extract-entities` (`02_Story_Bible/characters/`, `02_Story_Bible/locations/`, `02_Story_Bible/organizations/`, `02_Story_Bible/world-rules/`, `02_Story_Bible/secrets/`, `03_Development/tracker/`) so `plan-continuation`, `write-chapter`, `check-continuity`, and `finalize-chapter` operate without modification.

---

## 2. Step-by-Step Procedure

1. **Verify Approved `premise.md`:**
   Confirm `<Project>/03_Development/structure/premise/premise.md` exists and has been approved by Aurel.
2. **Propose Entities in Structured Batches:**
   Never dump hundreds of entities at once. Present in sequential review batches:
   - **Batch 1:** Core Cast (`02_Story_Bible/characters/`) with full names, aliases, and psychological flaws.
   - **Batch 2:** World Cosmology & Rules (`02_Story_Bible/world-rules/`, for both `type: fact` and `type: rule` notes).
   - **Batch 3:** Factions & Locations (`02_Story_Bible/organizations/`, `02_Story_Bible/locations/`).
   - **Batch 4:** Secrets & Hooks (`02_Story_Bible/secrets/`, `03_Development/tracker/`).
3. **Provenance Attribution:**
   - Explicitly stated by Aurel: `source.type: user_input`, `authority: user`, `confidence: 1.0`.
   - Proposed by AI: `source.type: inference`, `authority: ai`, `confidence: 0.8`. Once approved by Aurel, update `authority: user`.
4. **Name Collision Sweep:**
   Check proposed names against all existing projects using `vault_index.py --query "<name>" --include-fiction` to prevent accidental name collisions.
5. **Verify with `vault_doctor.py --include-fiction` and `vault_index.py --build --include-fiction`.**
- Include `- Used: worldbuild-original` in the handoff block.
