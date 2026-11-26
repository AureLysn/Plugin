---
name: dieu-phoi-hang-doi
description: "Drive a project's sequential task queue (hang-doi.json via giao_viec.py) one job at a time, enforcing single-agent execution without parallel agents. Built for systematic multi-arc chapter progression. Use when running an automated project queue ('chạy hàng đợi', 'điều phối hàng đợi', 'dieu-phoi-hang-doi', 'tự động giao việc')."
---

# `dieu-phoi-hang-doi` — Sequential Job Queue Orchestration

## 1. Operating Rules & Boundaries

- Implemented via `01_Origine/04_Tools/VaultTool/Tracking/giao_viec.py` reading `<Project>/00_Overview/hang-doi.json`.
- **Sequential Invariant (`[[13-agent-routing]]` §4):** Never run subagents in parallel. Dispatch **one** subagent at a time, wait for completion, run its gate, and record the result before advancing to the next job.
- **Stop Conditions:** Stop immediately and alert Aurel when:
  - An arc gate or human-review checkpoint is reached.
  - A job fails past `config.max_attempts`.
  - A canon or premise question arises that only Aurel can decide (`[[CLAUDE]]` §2).

---

## 2. Execution Loop (One Pass per Job)

1. **Check Queue Status:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/giao_viec.py status --project <CODE>
   ```
2. **Fetch Next Job:**
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/giao_viec.py next --project <CODE>
   ```
   `next` prints the job, its prompt and what it waits for. It also closes the approval stops that the queue's config switched off: the commit stop only when it is next and `chapter_gate.py`, run again, gives exit `0` with nothing waived; otherwise it waits for Aurel.
3. **Agent job: confirm model and effort with Aurel first** (once per day, or once for the batch with `--scope dot`). The tool refuses to start an agent job without it:
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/giao_viec.py confirm --project <CODE> --by Aurel --note "<model, effort>"
   ```
4. **Take the job** — only a job that was started can be closed, and only one runs at a time:
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/giao_viec.py start --project <CODE>
   ```
   - `kind: agent` → dispatch `xuong-lam` or `xuong-kiem` with the exact assigned skill and chapter path in the prompt. Wait for return.
   - `kind: main` → handle directly in the main session following the step's skill. The `fix` steps first run `finding_check.py` on the auditor's JSON block (`shared/working-standard.md` §5), then write its tables and the fixes into `ch<NN>-review.md` beside the chapter; `state_apply.py` needs that file later.
5. **Close the job** — the tool runs the step's gate, then records it:
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/giao_viec.py done --project <CODE> --note "<files, metrics>"
   python 01_Origine/04_Tools/VaultTool/Tracking/giao_viec.py done --project <CODE> --nang <N> --note "..."   # review: N = FAIL findings returned, proven or not; fix: N = proven ones not fixed + unproven ones not refuted
   ```
   A gate at exit `1` does not stop the queue, but `done` prints its verdict and logs it (`gate-warn`): read it before going on. After `write`, a POV place to read goes into the `check` step; after `fix` there is no further check, so it goes to Aurel at the commit stop (`[[09-gates]]` §2). The `write` and `fix` gates are `min_length` and `chapter_gate` (which runs `style_metrics`, `ai_tells_check` and `pov_leak_check`). `config.waived_gates` may name the gate or one of its three parts, with Aurel's reason; `done` prints and logs what was left out (`gate-waived`).
   A job that cannot be finished: `fail --project <CODE> --why "..."`; the queue stops. After the cause is fixed: `retry --project <CODE>` (at most `config.max_attempts`).
6. **Approval stops.** A `human` job opens only on Aurel's word:
   ```bash
   python 01_Origine/04_Tools/VaultTool/Tracking/giao_viec.py approve --project <CODE> --by Aurel --note "..."
   ```
   Exception (Aurel, 2026-10-25): when the queue's `config.auto_approve` is on, `auto --project <CODE>` approves the two stops **inside** a chapter (plan approval, commit approval) by itself, and only when the fix step left 0 serious findings and the measured gate passed: for the commit stop the tool runs `chapter_gate.py` again and refuses at exit `1`, while the gate, one of its parts or `min_length` is waived, or when the `state_apply` dry run names a note that does not exist. Each such approval is listed for Aurel under "Duyệt sau"; `seen --project <CODE> --by Aurel` clears the list once Aurel has looked. The arc gate is never approved this way.
7. **Loop until an approval stop, failure, or empty queue.**
- Include `- Used: dieu-phoi-hang-doi` in the handoff block.
