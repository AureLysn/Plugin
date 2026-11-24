#!/usr/bin/env python3
"""PreToolUse hook (Write / Edit / MultiEdit / NotebookEdit and Bash / PowerShell): ask
before the agent changes its own guardrails (0.8.0, plugin-benchmark-20261124 G6).

Guarded files: `CLAUDE.md` (any folder), every `hooks.json`, `.claude/settings.json` and
`.claude/settings.local.json` (user and project), `managed-settings.json`, `~/.claude.json`,
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, anything under
`~/.claude/plugins/` (installed plugins, marketplace registry) or a `.claude/hooks/` folder, and
the hook rules the vault-ops engine runs (`01_Origine/05_Meta/Rules/hook/`, V2).
Why: a change there can switch a guard off unseen — a BOM in two `hooks.json` files kept
every hook of two plugins unloaded from 2026-11-14 to 2026-11-23.
Not guarded: hook scripts in the vault copy of the plugins. They reach a session only after a
version bump, a PR and a sync, all approved by Aurel.

Ask, not block: plugin work edits these files legitimately, and the permission prompt is where
Aurel confirms (Claude Code: `permissionDecision: "ask"`; any other host: exit 2).
A shell command counts when it writes such a file: a `>` / `>>` redirection, `tee`,
`Out-File`, `Set-Content` / `Add-Content`, `cp` / `mv` / `Copy-Item` / `Move-Item` /
`Rename-Item`, `rm` / `Remove-Item`, `New-Item`, `touch`, `ln` — after unwrapping and
following `cd` and variables (`duong_dan.walk`, `duong_dan.written_files`). Reading one
(`cat`, `Get-Content`, `grep`) is not a change. Not covered: writes made inside scripts or
`python -c`, and the file tools of hosts other than Claude Code (their names are not recorded).

Exit 0 = allow (or ask, see above), 2 = block.
"""

from __future__ import annotations

import json
import os
import sys

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from duong_dan import Scope, walk, written_files
    from tach_lenh import shell_of, unreadable
    HELPERS = True
except Exception:  # helpers missing: this hook cannot judge paths, the fail mode decides
    HELPERS = False

    def unreadable(reason: str, default: int = 0) -> int:
        strict = os.environ.get("GIT_GUARD_STRICT", "").strip().lower() in ("1", "true", "yes", "on")
        return 2 if strict else default

FILE_TOOLS = {"write", "edit", "multiedit", "notebookedit"}
ASK_MSG = (
    "Sửa rào chắn của chính phiên — {label}.\n"
    "  File này bật hoặc tắt hook, quyền hay luật của phiên (plugin-benchmark-20261124 G6). Sửa nó có thể\n"
    "  tắt rào chắn mà không ai thấy: một BOM trong hai hooks.json đã làm hook của hai plugin không chạy\n"
    "  từ 14 đến 23/11/2026. Aurel xác nhận trong hộp hỏi nếu đây là việc đã giao."
)


def guarded(path: str) -> str | None:
    """What a normalised path guards, or None."""
    parts = path.split("/")
    base, parent = parts[-1], (parts[-2] if len(parts) > 1 else "")
    if "/.claude/plugins/" in path + "/":
        return "plugin đã cài"
    if "/.claude/hooks/" in path + "/":
        return "hook của Claude Code"
    if "/01_origine/05_meta/rules/hook/" in path + "/":
        return "luật hook của vault"
    if base == "claude.md":
        return "hợp đồng CLAUDE.md"
    if base == "hooks.json":
        return "cấu hình hook"
    if base in ("settings.json", "settings.local.json") and parent == ".claude":
        return "settings của Claude Code"
    if base in ("managed-settings.json", ".claude.json"):
        return "cấu hình Claude Code"
    if base in ("plugin.json", "marketplace.json") and parent == ".claude-plugin":
        return "manifest plugin"
    return None


def check_shell(cmd: str, cwd: str | None, shell: str | None) -> str | None:
    for c in walk(cmd, cwd, shell):
        for raw, path in written_files(c):
            why = guarded(path)
            if why:
                return f"{why}: `{raw}`"
    return None


def main() -> int:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace"))
    except Exception:
        return unreadable("stdin không phải JSON")
    ti = (data.get("tool_input") or data.get("toolInput")) if isinstance(data, dict) else None
    if not isinstance(ti, dict):
        return unreadable("không có tool_input")
    if not HELPERS:
        return unreadable("thiếu tach_lenh.py hoặc duong_dan.py")
    cwd = data.get("cwd") or data.get("currentWorkingDirectory") or os.getcwd()
    tool = str(data.get("tool_name") or data.get("toolName") or "").lower()
    try:
        if tool in FILE_TOOLS:
            raw = ti.get("file_path") or ti.get("notebook_path") or ""
            if not isinstance(raw, str):
                return unreadable("file_path không phải chuỗi")
            path = Scope(cwd).literal(raw) if raw else None
            why = guarded(path) if path else None
            label = f"{why}: `{raw}`" if why else None
        else:
            cmd = ti.get("command") or ti.get("CommandLine") or ""
            if not isinstance(cmd, str):
                return unreadable("command không phải chuỗi")
            label = check_shell(cmd, cwd, shell_of(data))
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
