---
name: research-genre
description: "Research recurring fandom tropes or broader genre conventions and record them as reusable reference maps in 05_Evasion/01_Oeuvre/Database/Fandom/<UNIVERSE>/Lore/ or 05_Evasion/01_Oeuvre/Database/Taxonomy/Genres/. Use when researching genre patterns ('tìm hiểu thể loại', 'nghiên cứu thể loại', 'research-genre', 'trope thường gặp', 'fan hay viết gì')."
---

# `research-genre` — Reusable Genre & Fandom Trope Mapping

## 1. Two Levels of Trope Maps

This skill builds **shared maps**, not project-specific choices (`analyze-tropes` maps where a project sits on a map):

| Map Type | Scope & Contents | Authoritative Location |
|---|---|---|
| **Fandom Trope Map** | Specific tropes, recurring AU premises, and relationship dynamics written within a fandom | `05_Evasion/01_Oeuvre/Database/Fandom/<UNIVERSE>/Lore/trope-fandom-<universe>.md` |
| **Genre Map** | Universally recurring conventions, beats, and clichés of a genre regardless of fandom | `05_Evasion/01_Oeuvre/Database/Taxonomy/Genres/<slug>.md` |

---

## 2. Map Structure & Honesty Invariant

Every trope map note (`type: info`, `canon_layer: fanon`, `authority: fandom`) must declare:
1. **Core Axes:** The defining variables every story in this genre must set (e.g., time travel: *who travels, how far back, physical vs consciousness, fixed vs mutable timeline*).
2. **Common Variants:** Recurring sub-genres and combinations.
3. **Expected Reader Beats:** Obligatory moments reader expectations demand (`[[setup-and-payoff]]`).
4. **Clichés & Fatigue Points:** Tropes the community considers overused or lazy.
5. **Subversion Directions:** Innovative ways authors have bent or inverted the genre.
6. **Evidence Labels (`[[AGENTS]]` Invariant 11):** Label every frequency assertion as `measured` (with tag count and date), `sourced` (citing Fanlore/TV Tropes), or `impression`.
- Include `- Used: research-genre` in the handoff block.
