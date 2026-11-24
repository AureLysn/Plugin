---
name: ghi-loi
description: "Convert a discovered AI tool quirk, gate blind spot, or workflow failure into a hook rule note (no code), a script check, a PreToolUse hook, or an entry in pre-handoff-verification-checklist.md and ai-tool-and-environment-quirks.md. Use when an error or false-positive gate is caught ('ghi lỗi', 'rút kinh nghiệm', 'thêm vào checklist')."
---

# `ghi-loi` — Error Mechanism Prevention & Checklist Update

> **Core Principle (`[[principles]]` Principle 2 & `[[09-gates]]`):**
> *Loading a rule is not enforcing it.* When a mistake happens more than once, do not write a longer narrative diary entry that no future session will read. Convert the lesson into a **hook rule**, a **gate**, a **`PreToolUse` hook**, or a **concrete verification item** in `[[pre-handoff-verification-checklist]]`.

---

## 1. Where Each Lesson Belongs in `D:\AureLysn`

| Type of Lesson | Authoritative Destination | Action Required |
|---|---|---|
| **Command, argument, file or edit that a regex can see** | `01_Origine/05_Meta/Rules/hook/<slug>.md` (`[[hook-rule-format]]`) | Write a hook rule note (§2); no Python, no version bump, no plugin sync |
| **Dangerous pattern that has to measure something** (a stale index, the branch, a path on disk) | `01_Origine/03_Systems/Plugin/git-guard/hooks/` or `vault-ops/hooks/` | Add or extend a `PreToolUse` hook (`exit 2` on match) + unit test in `test_chan_*.py`; it reaches sessions after a bump and a sync (`[[_SYSTEMS-MOC]]` §4.3) |
| **Schema / Frontmatter / Link / Claim blind spot** | `01_Origine/04_Tools/VaultTool/Core/vault_doctor.py` or `Validation/claim_check.py` | Add a check + negative regression test in `Validation/test_claim_check.py` |
| **OS / Encoding / Shell / Tooling quirk** | `01_Origine/05_Meta/Rules/global/ai-tool-and-environment-quirks.md` (`[[ai-tool-and-environment-quirks]]`) | Document the exact root cause and deterministic command pattern |
| **Pre-handoff verification check** | `01_Origine/05_Meta/Report/pre-handoff-verification-checklist.md` (`[[pre-handoff-verification-checklist]]`) | Add or update the verification row with its enforcement label (`gate` · `hook` · `inspection`) |

---

## 2. Writing a Hook Rule

1. Look for a rule that already covers it (`_RULES-MOC` §4) and read `[[hook-rule-format]]`.
2. Write the note with `status: draft`, `authority: ai`: symptom → root cause → check in prose, with dates and how often it happened, and one `toml` block with at least one `[[match]]` (the real call that failed) and one `[[pass]]` (a close call that is fine: the same words inside a quoted string, a comment or a search). Add the note to `_RULES-MOC` §4 and link it both ways (`related`).
3. Run `python 01_Origine/03_Systems/Plugin/vault-ops/hooks/chay_luat.py --check` (exit `0`; it names the condition that did not hold), then try the real command with `--try -` (the command on stdin, so that no shell changes its quotes).
4. A draft only logs. Propose `active` to Aurel when the mistake came back, or once if it was costly, with the numbers of `chay_luat.py --stats`; she decides (`[[hook-rule-format]]` §1). On approval set `status`, `authority`, `canon_layer` and `confidence` together. The rule takes effect when the branch is merged and pulled.

---

## 3. Procedure

1. Read the target file (`[[pre-handoff-verification-checklist]]`, `[[ai-tool-and-environment-quirks]]` or the rule note) before editing (`[[CLAUDE]]` Invariant 4).
2. State the failure mechanism concisely: **Symptom → Root cause → Deterministic check/hook that catches it**.
3. If a hook, a rule or a gate script was modified, run its tests (`test_chan_*.py`, `chay_luat.py --check`, or `test_claim_check.py` in the background) and verify `exit 0` (`executed`).
4. Rebuild the index (`vault_index.py --build --include-fiction`; in a worktree as `kiem-tra-he-thong` step 1 says) and run `vault_doctor.py --include-fiction`, which checks the hook rules too.
- Include `- Used: ghi-loi` in the handoff block.
