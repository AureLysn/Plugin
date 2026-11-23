---
name: doi-chieu-thu-vien
description: "Compare a project's style profile (or global writing rules) against the general writing craft library in 01_Origine/02_Knowledge/Curated_Notes/writing/ to identify unrecorded deviations or gaps. Use when auditing style completeness ('đối chiếu thư viện', 'doi-chieu-thu-vien', 'style còn thiếu gì', 'so với nguyên tắc chung')."
---

# `doi-chieu-thu-vien` — Style vs Writing Craft Library Gap Analysis

## 1. Precedence Principle (`[[03-precedence]]` & `[[rule-protocol]]`)

- A project's deliberate style choices (`02_Story_Bible/style/`) override general writing advice in `01_Origine/02_Knowledge/Curated_Notes/writing/`, **provided the break is deliberate and documented**.
- This skill identifies where a style profile is silent or breaks a craft rule without recording why. It **never** edits style notes or rules automatically.

---

## 2. Rule Classification Matrix

Compare each rule in `01_Origine/02_Knowledge/Curated_Notes/writing/` against the project's `02_Story_Bible/style/` files:

| Classification | Meaning | Action |
|---|---|---|
| **Covered** | The style explicitly affirms this rule | Cite the covering line |
| **Deliberate Break** | The style breaks the rule **and states why** (or the source author does in continuation) | Cite the line and reason — no action |
| **Unrecorded Break** | The style breaks the rule with no stated reason | 🟡 Flag as gap: either record the reason or revise |
| **Silent** | The style says nothing either way | ⚪ Note as optional candidate |
| **Floor Broken** | Breaks a `strength: hard` floor rule | 🔴 Blocking error: ask Aurel |

---

## 3. Output Report

In Vietnamese, present a clean Markdown table (`Rule · Classification · Evidence · Recommendation`), followed by:
1. **Gaps worth deciding:** Unrecorded breaks first, followed by relevant silent rules.
2. **Covered & deliberate breaks count.**
- Include `- Used: doi-chieu-thu-vien` in the handoff block.
