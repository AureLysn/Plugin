#!/usr/bin/env python3
"""PreToolUse hook (Bash / PowerShell): ask before deleting for good (0.8.0).

CLAUDE.md Invariant 3: permanent deletion needs an explicit request from Aurel, and
`git-an-toan` §3 lists `rm` on a vault note or storage file. Until 0.8.0 no hook enforced it
(plugin-benchmark-20261124 N4).

Ask Aurel (Claude Code: `permissionDecision: "ask"`; any other host: exit 2) when a command
deletes
  - anything inside the vault, a worktree or a store (`D:\\AureLysn`, `D:\\AureLysn-wt`,
    `G:\\My Drive\\AureLysn`), or a folder that holds one of them;
  - a folder with its contents anywhere else,
unless the target is in the session scratchpad, a temp folder or a cache folder
(`__pycache__`, `node_modules`, …). A target the hook cannot resolve (a variable it did not
see assigned) counts as risky when the delete is recursive or the command runs in the vault.

Delete commands: `rm`, `unlink`, `shred`, `rmdir`/`rd` and `del`/`erase` (cmd `/s`),
`Remove-Item` and its aliases, `find … -delete` or `-exec rm`, `robocopy … /MIR` or `/PURGE`
(deletes in the destination), `[IO.Directory]::Delete(…)` and `[IO.File]::Delete(…)`.
Commands handed to another program are unwrapped first, and `cd` and variables set earlier in
the same command are followed, into `if { }` bodies and subshells too (`duong_dan.walk`). Not
covered: deletes run inside scripts or `python -c` (`shutil.rmtree`, `os.remove`), and `git rm`.

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
    from duong_dan import Scope, holds_protected, protected, scratch_or_cache, walk
    from tach_lenh import decode, program_name, shell_of, unreadable
    HELPERS = True
except Exception:  # helpers missing: this hook cannot judge paths, the fail mode decides
    HELPERS = False

    def unreadable(reason: str, default: int = 0) -> int:
        strict = os.environ.get("GIT_GUARD_STRICT", "").strip().lower() in ("1", "true", "yes", "on")
        return 2 if strict else default

DELETERS = {"rm", "unlink", "shred", "rmdir", "rd", "del", "erase", "remove-item", "ri"}
CMD_STYLE = {"rmdir", "rd", "del", "erase"}  # take /s switches in cmd.exe
PS_PARAMS = {  # Remove-Item parameter -> role
    "recurse": "recurse", "path": "path", "literalpath": "path", "pspath": "path", "lp": "path",
    "filter": "value", "include": "value", "exclude": "value", "credential": "value",
    "stream": "value", "force": "flag", "whatif": "flag", "confirm": "flag",
}
DOTNET_DELETE = re.compile(r"\[(?:System\.)?IO\.(Directory|File)\]::Delete\(\s*(\"[^\"]*\"|'[^']*'|\$\w+)?", re.I)

ASK_MSG = (
    "Xoá vĩnh viễn: {label}.\n"
    "  CLAUDE.md bất biến 3 và `git-an-toan` §3: xoá vĩnh viễn trong vault, worktree hay kho chỉ làm\n"
    "  khi Aurel đồng ý rõ trong lượt này; ngoài vault, xoá cả thư mục cũng phải hỏi.\n"
    "  Cách khác: chuyển vào `_to_delete/<YYYY-MM-DD>/` (backup-and-recovery), hoặc làm trong scratchpad của phiên."
)


def option_role(v: str) -> str:
    """Role of an option word of a delete command: recurse, path, value or flag."""
    if v.startswith("--"):
        return "recurse" if v == "--recursive" else "flag"
    name = v[1:].split(":", 1)[0].lower()
    if len(name) >= 2:
        for full, role in PS_PARAMS.items():
            if full.startswith(name):
                return role
    return "recurse" if "r" in name else "flag"  # POSIX cluster: -r, -rf, -fr, -R


def split_list(v: str) -> list[str]:
    return [p for p in v.split(",") if p.strip()]


def delete_call(name: str, toks: list, k: int) -> tuple[bool, list[str]] | None:
    """(recursive, target words) when the command at toks[k] deletes something, else None."""
    args = toks[k + 1:]
    if name in DELETERS:
        recursive, targets, i, opts_done = False, [], 0, False
        while i < len(args):
            t, v = args[i], args[i].value
            i += 1
            if not opts_done and not t.quoted:
                if v == "--":
                    opts_done = True
                    continue
                if name in CMD_STYLE and re.fullmatch(r"/[a-zA-Z](?::\S*)?", v):
                    recursive |= v.lower() == "/s"
                    continue
                if v.startswith("-") and len(v) > 1:
                    role = option_role(v)
                    if role == "recurse":
                        recursive = True
                    elif role in ("path", "value") and i < len(args):
                        if role == "path":
                            targets += split_list(args[i].value)
                        i += 1
                    continue
            targets += split_list(v)
        return recursive, targets
    if name == "find":
        roots: list[str] = []
        rest: list[str] = []
        for j, t in enumerate(args):
            if not t.quoted and t.value.startswith(("-", "(", "!")):
                rest = [a.value for a in args[j:]]
                break
            roots.append(t.value)
        execs = [j for j, v in enumerate(rest) if v in ("-exec", "-execdir", "-ok", "-okdir")]
        if "-delete" in rest or any(j + 1 < len(rest) and program_name(rest[j + 1]) in ("rm", "shred", "unlink")
                                    for j in execs):
            return True, roots or ["."]
        return None
    if name == "robocopy":
        switches = {t.value.upper() for t in args if not t.quoted and t.value.startswith("/")}
        paths = [t.value for t in args if t.quoted or not t.value.startswith("/")]
        if switches & {"/MIR", "/PURGE"} and len(paths) >= 2:
            return True, [paths[1]]
    return None


def judge(recursive: bool, targets: list[str], scope: Scope) -> str | None:
    """Why this delete needs Aurel, or None."""
    for raw in targets:
        path = scope.resolve(raw)
        if path is None:
            if recursive or scope.cwd_protected():
                return f"đích chưa rõ `{raw}`"
            continue
        if scratch_or_cache(path):
            continue
        if protected(path) or holds_protected(path):
            return f"`{raw}` (trong vault, worktree hoặc kho)"
        if recursive:
            return f"`{raw}` (xoá cả thư mục, ngoài vùng nháp)"
    return None


def check(cmd: str, cwd: str | None, shell: str | None) -> str | None:
    for c in walk(cmd, cwd, shell):
        call = delete_call(c.program, c.toks, c.k) if c.program else None
        reason = judge(*call, c.scope) if call else None
        if reason:
            return f"{c.program} {reason}"
        for m in DOTNET_DELETE.finditer(c.text):
            raw = decode((m.group(2) or "").strip("'\"")) or "$?"
            reason = judge(m.group(1).lower() == "directory", [raw], c.scope)
            if reason:
                return f"[IO.{m.group(1)}]::Delete {reason}"
    return None


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
    if not HELPERS:
        return unreadable("thiếu tach_lenh.py hoặc duong_dan.py")
    cwd = data.get("cwd") or data.get("currentWorkingDirectory") or os.getcwd()
    try:
        label = check(cmd, cwd, shell_of(data))
    except Exception as e:
        return unreadable(f"lỗi khi kiểm: {type(e).__name__}: {e}", default=1)
    if not label:
        return 0
    msg = ASK_MSG.format(label=label)
    if "hook_event_name" in data:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": msg,
            }
        }, ensure_ascii=False))
        return 0
    print("CHẶN: " + msg, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
