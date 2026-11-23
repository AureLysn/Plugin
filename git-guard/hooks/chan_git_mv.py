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
        data = json.load(sys.stdin)
    except Exception:
        return 0
    ti = data.get("tool_input") or data.get("toolInput") or {}
    cmd = ti.get("command") or ti.get("CommandLine") or ""
    msg = check(cmd)
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
