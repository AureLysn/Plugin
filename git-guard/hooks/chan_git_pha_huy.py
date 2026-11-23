#!/usr/bin/env python3
"""PreToolUse hook (Bash / PowerShell): guard destructive Git commands.

Hard block (exit 2) — blanket staging, banned by `nhanh-va-commit` §3:
  `git add -A` / `--all` / `.` / `./` / `:/` / `:(top)` / `*`

Ask Aurel — the commands `git-an-toan` §3 allows only with Aurel's explicit confirmation:
  `git reset --hard`, `git checkout [--] .`, `git restore .` (worktree), `git clean -f…`,
  `git push --force` / `-f` / `--force-with-lease` / `+refspec`, `git branch -D`.
  Claude Code payload (has `hook_event_name`): exit 0 with `permissionDecision: "ask"`,
  so the permission prompt is Aurel's confirmation.
  Any other host (Google Antigravity, which only reads exit codes): exit 2.

Only the command word of each segment counts: a quoted string, a heredoc body or
`echo git add -A` is not a Git command. Unreadable input fails open (exit 0), as in the
other hooks of this plugin.

Exit 0 = allow (or ask, see above), 2 = block.
"""

from __future__ import annotations

import json
import re
import sys

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", re.S)
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
SPLIT_SEG = re.compile(r"(?:;|&&|\|\||\||&|\n)+")
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

ADD_ALL = {".", "./", ":/", ":(top)", ":/*", "*", "-A", "--all"}
WHOLE_TREE = {".", "./", ":/", ":(top)", ":/*", "*"}


def short_flags(args: list[str]) -> str:
    """Letters of the combined short flags (`-xdf` -> 'xdf')."""
    return "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--") and len(a) > 1)


def git_call(seg: str) -> tuple[str, list[str]] | None:
    toks = seg.split()
    i = 0
    while i < len(toks) and (toks[i] in ("&", "env", "command") or ENV_ASSIGN.match(toks[i])):
        i += 1
    if i >= len(toks):
        return None
    head = toks[i].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if head not in ("git", "git.exe"):
        return None
    j = i + 1
    while j < len(toks) and toks[j].startswith("-"):
        j += 2 if toks[j] in GLOBAL_OPTS_WITH_VALUE else 1
    if j >= len(toks):
        return None
    return toks[j], toks[j + 1:]


def classify(sub: str, args: list[str]) -> tuple[str, str] | None:
    """Return ('block'|'ask', label) or None."""
    flags = short_flags(args)
    argset = set(args)
    if sub == "add":
        if argset & ADD_ALL or "A" in flags:
            return "block", "git add -A / git add . (stage cả cây)"
        return None
    if sub == "reset" and "--hard" in argset:
        return "ask", "git reset --hard"
    if sub == "checkout" and argset & WHOLE_TREE:
        return "ask", "git checkout -- . (bỏ mọi thay đổi chưa commit)"
    if sub == "restore" and argset & WHOLE_TREE:
        staged_only = ("--staged" in argset or "S" in flags) and not ("--worktree" in argset or "W" in flags)
        if not staged_only:
            return "ask", "git restore . (bỏ mọi thay đổi chưa commit)"
        return None
    if sub == "clean":
        dry = "--dry-run" in argset or "n" in flags
        if not dry and ("--force" in argset or "f" in flags):
            return "ask", "git clean -f (xoá file chưa theo dõi)"
        return None
    if sub == "push":
        if any(a == "--force" or a.startswith("--force-with-lease") or a == "--force-if-includes" for a in args) \
                or "f" in flags or any(a.startswith("+") for a in args):
            return "ask", "git push --force (ghi đè lịch sử trên remote)"
        return None
    if sub == "branch":
        if "D" in flags or (("--delete" in argset or "d" in flags) and ("--force" in argset or "f" in flags)):
            return "ask", "git branch -D (xoá nhánh chưa merge)"
        return None
    return None


def check(cmd: str) -> tuple[str, str] | None:
    stripped = QUOTED.sub('""', HEREDOC.sub("", cmd))
    found: tuple[str, str] | None = None
    for seg in SPLIT_SEG.split(stripped):
        call = git_call(seg.strip())
        if not call:
            continue
        hit = classify(*call)
        if hit and (found is None or hit[0] == "block"):
            found = hit
            if hit[0] == "block":
                break
    return found


BLOCK_MSG = (
    "CHẶN: {label}.\n"
    "  Không stage cả cây làm việc (`nhanh-va-commit` §3): dễ kéo theo file rác, file bí mật\n"
    "  hoặc thay đổi của phiên khác vào commit.\n"
    "  Cách đúng: `git add <file-1> <file-2> …` theo đúng danh sách đã kiểm, rồi `git diff --cached --stat`."
)
ASK_MSG = (
    "{label}: lệnh này xoá hoặc ghi đè công việc và không hoàn tác được dễ dàng.\n"
    "  `git-an-toan` §3 chỉ cho chạy khi Aurel xác nhận rõ trong lượt này.\n"
    "  Trước đó: xem `git status` / `git stash list`; khi kẹt, dùng skill `git-cuu-ho`."
)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    ti = data.get("tool_input") or data.get("toolInput") or {}
    cmd = ti.get("command") or ti.get("CommandLine") or ""
    hit = check(cmd)
    if not hit:
        return 0
    kind, label = hit
    if kind == "ask" and "hook_event_name" in data:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": ASK_MSG.format(label=label),
            }
        }, ensure_ascii=False))
        return 0
    msg = BLOCK_MSG.format(label=label) if kind == "block" else "CHẶN: " + ASK_MSG.format(label=label)
    print(msg, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
