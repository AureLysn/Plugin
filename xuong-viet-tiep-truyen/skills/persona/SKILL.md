---
name: persona
description: "Create or adapt an original character/persona (OC) that spans multiple fandoms or story projects, maintaining base invariants in Database/Fandom/Personas/ and universe variants in Project-canon/. Use when designing or adapting an OC ('tạo persona', 'persona', 'OC của mình', 'persona variant')."
---

# `persona` — Cross-Universe Persona & OC Adaptation

## 1. Architecture: Base Persona vs Universe Variant

A persona transcends any single story project:
- **Base Persona Note:** Lives in `05_Evasion/01_Oeuvre/Database/SI_OC/<Persona>/<name>.md` (`type: persona`, `scope: universe` or `global`, `lane: personal`). Contains **only invariants**: core psychology, baseline temperament, moral lines, speech patterns, and fundamental fears.
- **Universe Variant Note:** Lives in `<Project>/02_Story_Bible/characters/<name>.md` (`type: character`, `scope: project`). Declares local attributes: age, local abilities/magic/flames, social standing, and universe-specific relationships.

---

## 2. Invariant Protection Rule

- **Never edit the base persona note to fit a single project.** If a trait must change to fit a specific universe, that trait is not an invariant — move it down to the project variant.
- In Vietnamese fiction, specify bidirectional address forms per relationship:
  ```yaml
  addressing:
    <CharacterA>: {self: tôi, other: cậu}
    <CharacterB>: {self: em, other: anh}
  ```

---

## 3. Verification & Gate

Run `vault_doctor.py --include-fiction` to ensure the variant links to the base persona and no cross-lane errors exist.
- Include `- Used: persona` in the handoff block.
