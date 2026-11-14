---
name: crossover-contract
description: "Establish or audit a formal crossover contract between two or more fandom universes, defining power system conversion rules, timeline anchors, and canon priority. Use when merging or crossing universes ('làm crossover', 'hợp đồng crossover', 'crossover-contract', 'ghép hai thế giới')."
---

# `crossover-contract` — Multi-Universe Crossover Governance

## 1. Operating Principle

Two fictional universes meeting is a set of explicit rules, not an aesthetic vibe. Settle all six core contract terms before drafting any prose.

---

## 2. Six Mandatory Contract Terms

Draft `<Project>/05_Management/contracts/crossover.md` (`id: rule.<CODE>.crossover`, `type: rule`, `strength: hard`, `scope: project`, `always_load: true` on crossover scenes):

1. **`universes:`** Explicit list of source fandom codes declared in `Database/Fandom/<UNIVERSE>/`.
2. **`interaction.mode:`** `travel` (characters move between worlds), `merge` (histories fused into one reality), or `parallel` (coexisting with portals/mirrors).
3. **`timeline:`** Exact in-canon timestamp where each universe sits at the moment of contact.
4. **`memory:`** Do characters retain full memories of their home worlds?
5. **`power_policy:`**
   - **Default:** Power systems are **inconvertible** (e.g., dying will flames ≠ cursed energy ≠ chakra). A character may learn to perceive an alien energy without automatically gaining its techniques.
   - `direct_scaling: false` by default — arbitrary power-level equality collapses narrative tension.
6. **`canon_priority:`** When physical or cosmological laws conflict, which universe's rules govern local space?

---

## 3. Verification & Gate

Run `vault_doctor.py --include-fiction` to verify all declared universes resolve to existing `Database/Fandom/<UNIVERSE>/` notes.
- Include `- Used: crossover-contract` in the handoff block.
