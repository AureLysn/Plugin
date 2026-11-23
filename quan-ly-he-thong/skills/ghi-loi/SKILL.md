---
name: ghi-loi
description: "Convert a discovered AI tool quirk, gate blind spot, or workflow failure into a deterministic PreToolUse hook, script check, or entry in pre-handoff-verification-checklist.md and ai-tool-and-environment-quirks.md. Use when an error or false-positive gate is caught ('ghi lỗi', 'rút kinh nghiệm', 'thêm vào checklist')."
---

# `ghi-loi` — Error Mechanism Prevention & Checklist Update

> **Core Principle (`[[principles]]` Principle 2 & `[[09-gates]]`):**
> *Loading a rule is not enforcing it.* When a mistake happens more than once, do not write a longer narrative diary entry that no future session will read. Convert the lesson into a **gate**, a **`PreToolUse` hook**, or a **concrete verification item** in `[[pre-handoff-verification-checklist]]`.

---

## 1. Where Each Lesson Belongs in `D:\AureLysn`

| Type of Lesson | Authoritative Destination | Action Required |
|---|---|---|
| **Dangerous Bash / Git command pattern** | `01_Origine/03_Systems/Plugin/git-chung/hooks/` or `quan-ly-he-thong/hooks/` | Add or extend a `PreToolUse` hook (`exit 2` on match) + unit test in `test_chan_*.py` |
| **Schema / Frontmatter / Link / Claim blind spot** | `01_Origine/04_Tools/VaultTool/Core/vault_doctor.py` or `Validation/claim_check.py` | Add a check + negative regression test in `Validation/test_claim_check.py` |
| **OS / Encoding / Shell / Tooling quirk** | `01_Origine/05_Meta/Rules/global/ai-tool-and-environment-quirks.md` (`[[ai-tool-and-environment-quirks]]`) | Document the exact root cause and deterministic command pattern |
| **Pre-handoff verification check** | `01_Origine/05_Meta/Report/pre-handoff-verification-checklist.md` (`[[pre-handoff-verification-checklist]]`) | Add or update the verification row with its enforcement label (`gate` · `hook` · `inspection`) |

---

## 2. Procedure

1. Read the target file (`[[pre-handoff-verification-checklist]]` or `[[ai-tool-and-environment-quirks]]`) before editing (`[[CLAUDE]]` Invariant 4).
2. State the failure mechanism concisely: **Symptom → Root cause → Deterministic check/hook that catches it**.
3. If a hook or gate script was modified, run its unit test suite (`test_chan_*.py` or `test_claim_check.py`) and verify `exit 0` (`executed`).
4. Rebuild the index (`vault_index.py --build --include-fiction`) and run `vault_doctor.py --include-fiction`.
- Include `- Used: ghi-loi` in the handoff block.
