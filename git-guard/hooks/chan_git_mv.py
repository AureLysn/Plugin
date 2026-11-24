#!/usr/bin/env python3
"""PreToolUse hook (Bash): block git mv on Markdown notes (.md).

Renaming a vault note via `git mv` updates the filename on disk without updating
inbound `[[wikilinks]]` across the vault (CLAUDE.md Invariant 10).

Exit 0 = allow, 2 = block (stderr shown to Claude).
"""

from __future__ import annotations

import json
import re
import sys

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from tach_lenh import shell_of, unreadable, variants  # shared reading and fail mode (0.8.0)
except Exception:  # helper missing: raw command only; GIT_GUARD_STRICT still honoured
    import os as _os

    def variants(cmd: str, shell: str | None = None) -> list[str]:
        return [cmd]

    def shell_of(data: object) -> str | None:
        return None

    def unreadable(reason: str, default: int = 0) -> int:
        strict = _os.environ.get("GIT_GUARD_STRICT", "").strip().lower() in ("1", "true", "yes", "on")
        return 2 if strict else default

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", re.S)
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')


def strip_inert(cmd: str) -> str:
    """Remove heredoc bodies and quoted strings so commit messages do not trigger false positives."""
    s = HEREDOC.sub("", cmd)
    return QUOTED.sub('""', s)


GIT_MV = re.compile(r"(?:^|[;&|]\s*|\b)git\s+(?:\S+\s+)*mv\b([^\n;|&]*)")


def check(cmd: str) -> str | None:
    s = strip_inert(cmd)
    for m in GIT_MV.finditer(s):
        # Inspect the unstripped tail around the match so quoted ".md" paths are still caught
        start = m.start()
        raw_tail = cmd[start:start + 400].splitlines()[0]
        if re.search(r"\.md\b", raw_tail, re.I):
            return (
                "CHẶN: không dùng `git mv` trên note `.md` (CLAUDE.md bất biến 10).\n"
                "  Đổi tên bằng git không cập nhật wikilink trỏ tới file đó.\n"
                "  Cách đúng:\n"
                "    1. Đổi tên trong Obsidian (tự sửa mọi wikilink), HOẶC\n"
                "    2. Tìm toàn bộ `[[tên-cũ]]` bằng vault_index.py / Grep, sửa hết,\n"
                "       thêm tên cũ vào `aliases:` của note, rồi chạy `vault_doctor.py`."
            )
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
    try:
        msg = None
        for v in variants(cmd, shell_of(data)):
            msg = check(v)
            if msg:
                break
    except Exception as e:
        return unreadable(f"lỗi khi kiểm: {type(e).__name__}: {e}", default=1)
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
