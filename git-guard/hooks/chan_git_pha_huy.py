#!/usr/bin/env python3
"""PreToolUse hook (Bash / PowerShell): guard destructive Git commands.

Hard block (exit 2) — blanket staging, banned by `nhanh-va-commit` §3:
  `git add -A` / `--all` / `.` / `./` / `:/` / `:(top)` / `*`

Ask Aurel — the commands `git-an-toan` §3 allows only with Aurel's explicit confirmation:
  `git reset --hard`, `git checkout [--] .`, `git restore .` (worktree), `git clean -f…`,
  `git push --force` / `-f` / `--force-with-lease` / `+refspec`, `git branch -D`,
  `git stash drop` / `git stash clear`, `git worktree remove --force` (the last three since 0.8.0),
  and `git worktree remove <path>` while another checkout is nested in that worktree: Git looks
  only at its own files there, so a gitignored nested checkout (`04_Portfolio/`, `05_Evasion/`,
  `git-an-toan` §4) goes with it, uncommitted files included (executed 2026-11-24; 0.8.0).
  Claude Code payload (has `hook_event_name`): exit 0 with `permissionDecision: "ask"`,
  so the permission prompt is Aurel's confirmation.
  Any other host (Google Antigravity, which only reads exit codes): exit 2.

Only the command word of each segment counts: a quoted string, a heredoc body or
`echo git add -A` is not a Git command. A command handed to another program
(`bash -c "…"`, `powershell -Command "…"`, `cmd /c …`, `& "…\\git.exe"`, `Start-Process`,
`time …`) is unwrapped by `tach_lenh.variants` and checked too (0.8.0). Unreadable input
fails open (exit 0), as in the other hooks of this plugin, unless `GIT_GUARD_STRICT=1`
is set: then it blocks (`tach_lenh.unreadable`, 0.8.0).

Exit 0 = allow (or ask, see above), 2 = block.
"""

from __future__ import annotations

import json
import os
import re
import sys

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from tach_lenh import shell_of, unreadable, variants  # shared reading and fail mode (0.8.0)
except Exception:  # helper missing: raw command only; GIT_GUARD_STRICT still honoured
    def variants(cmd: str, shell: str | None = None) -> list[str]:
        return [cmd]

    def shell_of(data: object) -> str | None:
        return None

    def unreadable(reason: str, default: int = 0) -> int:
        strict = os.environ.get("GIT_GUARD_STRICT", "").strip().lower() in ("1", "true", "yes", "on")
        return 2 if strict else default

try:
    from duong_dan import Scope, walk  # paths, for nested checkouts only (0.8.0)
    PATHS = True
except Exception:
    PATHS = False

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
    action = next((a for a in args if not a.startswith("-")), "")
    if sub == "stash" and action in ("drop", "clear"):
        return "ask", f"git stash {action} (xoá stash, rất khó lấy lại)"
    if sub == "worktree" and action == "remove" and ("--force" in argset or "f" in flags):
        return "ask", "git worktree remove --force (xoá worktree kèm thay đổi chưa commit)"
    return None


def removed_worktree(words: list[str], scope: Scope) -> str | None:
    """Absolute path of the worktree in `git [-C dir] worktree remove <path>`, else None."""
    i = 0
    while i < len(words) and words[i].startswith("-"):
        if words[i] == "-C" and i + 1 < len(words):
            scope = Scope(scope.resolve(words[i + 1]))
        i += 2 if words[i] in GLOBAL_OPTS_WITH_VALUE else 1
    args = [w for w in words[i + 1:] if not w.startswith("-")]
    if words[i:i + 1] != ["worktree"] or args[:1] != ["remove"] or len(args) < 2:
        return None
    return scope.resolve(args[1])


def nested_checkouts(cmd: str, cwd: str | None, shell: str | None) -> str | None:
    """Label when a `git worktree remove` takes Git checkouts nested in that worktree with it.

    A worktree named by its last path component only (`remove <slug>`) is not resolved.
    """
    for c in walk(cmd, cwd, shell):
        if c.program != "git":
            continue
        path = removed_worktree([t.value for t in c.args], c.scope)
        if path is None or not os.path.isdir(path):
            continue
        nested = [d for d in sorted(os.listdir(path)) if os.path.exists(os.path.join(path, d, ".git"))]
        if nested:
            return (f"git worktree remove (bên trong còn checkout lồng: {', '.join(nested)}; "
                    "chúng bị xoá theo, kể cả file chưa commit, dù không có --force. "
                    "Gỡ từng checkout lồng trước: `pr-va-merge` §3)")
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
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace"))
    except Exception:
        return unreadable("stdin không phải JSON")
    ti = (data.get("tool_input") or data.get("toolInput")) if isinstance(data, dict) else None
    if not isinstance(ti, dict):
        return unreadable("không có tool_input")
    cmd = ti.get("command") or ti.get("CommandLine") or ""
    if not isinstance(cmd, str):
        return unreadable("command không phải chuỗi")
    cwd = data.get("cwd") or data.get("currentWorkingDirectory") or os.getcwd()
    try:
        hit = None
        for v in variants(cmd, shell_of(data)):
            h = check(v)
            if h and (hit is None or h[0] == "block"):
                hit = h
                if h[0] == "block":
                    break
        if hit is None and PATHS:
            label = nested_checkouts(cmd, cwd, shell_of(data))
            hit = ("ask", label) if label else None
    except Exception as e:
        return unreadable(f"lỗi khi kiểm: {type(e).__name__}: {e}", default=1)
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
