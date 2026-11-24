#!/usr/bin/env python3
"""SessionStart and PreCompact hook: keep the handoff in view across a fresh start or a
compaction (vault-ops 0.10.0; plugin-benchmark-20261124 V1, which closes G7 and G8).

SessionStart (`startup`, `resume`, `clear`, `compact`): adds a short context block — the
vault's branch and count of uncommitted files, the other worktrees, and a pointer to the
`session-handoff` note with the time it was last changed. After `compact` or `resume` it
also says to re-read the handoff and `git status` before editing on. It names the hook rules of
the vault that `chay_luat.py --check` would report (most of them are not run).
PreCompact: prints what the compaction summary has to keep (branch and worktree in use,
files changed but not committed, what is done and not done with executed / inspected /
assumed labels, questions waiting for Aurel) and a reminder to run `ban-giao` before the
session ends.

Pointers only, never note content, so the lane rules of CLAUDE.md Invariant 6 hold. It never
blocks: any error prints nothing and exits 0. Output is capped at 1,500 characters. Outside
the vault (no `CLAUDE.md` next to `01_Origine/` above the working directory) it is silent.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LIMIT = 1500
HANDOFF = Path("06_Station/01_Daily_Logs/session-handoff.md")

PRECOMPACT_HEAD = (
    "[vault-ops] Khi tóm tắt ngữ cảnh, giữ lại:\n"
    "- nhánh và worktree đang làm, commit đã tạo và đã push hay chưa;\n"
    "- file đã sửa nhưng chưa commit;\n"
    "- việc đã xong và chưa xong, kèm nhãn executed / inspected / assumed;\n"
    "- câu hỏi đang chờ Aurel và quyết định Aurel đã đưa trong phiên.\n"
    "Trạng thái lúc tóm tắt:"
)
PRECOMPACT_TAIL = "Trước khi kết thúc phiên: chạy skill vault-ops `ban-giao` để cập nhật [[session-handoff]]."
RESUME_NOTE = ("- Ngữ cảnh vừa được tóm tắt hoặc mở lại: đọc lại handoff và chạy `git status` / "
               "`git worktree list` trước khi sửa tiếp; đừng dựa vào trí nhớ về file đã sửa.")


def find_vault(start: Path) -> Path | None:
    for c in [start, *start.parents]:
        if (c / "CLAUDE.md").is_file() and (c / "01_Origine").is_dir():
            return c
    return None


def git(args: list[str], cwd: Path) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=5)
    except Exception:
        return None
    return r.stdout if r.returncode == 0 else None


def worktrees(vault: Path) -> list[tuple[str, str]]:
    """(path, branch) of every worktree except the one at `vault`."""
    out = git(["worktree", "list", "--porcelain"], vault) or ""
    here = vault.resolve().as_posix().lower()
    found: list[tuple[str, str]] = []
    for block in out.strip().split("\n\n"):
        path, branch = "", "detached"
        for line in block.splitlines():
            if line.startswith("worktree "):
                path = line[9:].strip()
            elif line.startswith("branch "):
                branch = line[7:].strip().removeprefix("refs/heads/")
        if path and Path(path).resolve().as_posix().lower() != here:
            found.append((path, branch))
    return found


def state_lines(vault: Path) -> list[str]:
    lines: list[str] = []
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], vault)
    if branch is not None:
        status = git(["status", "--porcelain", "--untracked-files=all"], vault) or ""
        n = len([ln for ln in status.splitlines() if ln.strip()])
        lines.append(f"- `{vault}`: nhánh `{branch.strip()}`, " + (f"{n} file chưa commit" if n else "không có thay đổi chưa commit"))
    others = worktrees(vault)
    if others:
        shown = ", ".join(f"`{p}` [{b}]" for p, b in others[:5])
        more = f" và {len(others) - 5} worktree nữa" if len(others) > 5 else ""
        lines.append(f"- Worktree khác: {shown}{more}")
    handoff = vault / HANDOFF
    if handoff.is_file():
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(handoff.stat().st_mtime))
        lines.append(f"- Bàn giao gần nhất: [[session-handoff]] (`{HANDOFF.as_posix()}`, sửa lúc {stamp}).")
    return lines


def broken_rules(vault: Path) -> list[str]:
    """One line naming the hook rules that `chay_luat.py --check` would report."""
    try:
        from chay_luat import RULES_REL, broken, main_tree
        tree = main_tree(str(vault))
        names = broken(tree) if tree and (tree / RULES_REL).is_dir() else []
    except Exception:
        return []
    if not names:
        return []
    more = f" và {len(names) - 8} luật nữa" if len(names) > 8 else ""
    return [f"- Luật hook có lỗi, có thể không chạy: {', '.join(f'`{n}`' for n in names[:8])}{more}. "
            "Xem lỗi: `python 01_Origine/03_Systems/Plugin/vault-ops/hooks/chay_luat.py --check`."]


def main() -> int:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace"))
        event = data.get("hook_event_name") or ""
        cwd = Path(data.get("cwd") or os.getcwd())
        vault = find_vault(cwd.resolve())
        if vault is None:
            return 0
        lines = state_lines(vault)
        if event == "PreCompact":
            print("\n".join([PRECOMPACT_HEAD, *lines, PRECOMPACT_TAIL])[:LIMIT])
        elif event == "SessionStart":
            source = str(data.get("source") or "startup")
            parts = [f"[vault-ops] Trạng thái lúc mở phiên ({source}):", *lines, *broken_rules(vault)]
            if source in ("compact", "resume"):
                parts.append(RESUME_NOTE)
            context = "\n".join(parts)[:LIMIT]
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                     "additionalContext": context}}, ensure_ascii=False))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
