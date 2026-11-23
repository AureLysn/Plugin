#!/usr/bin/env python3
"""PreToolUse hook (Bash): block writing or running temporary scripts in $TEMP / /tmp.

The session scratchpad (a path with a `scratchpad` folder in it) is allowed: it is where scratch
scripts belong (Aurel, 2026-11-13; ai-tool-and-environment-quirks §3.4).

Exit 0 = allow, 2 = block.
"""

from __future__ import annotations

import json
import re
import sys

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Group 2 is the rest of the heredoc's first line (`> /tmp/run.py`); only the body is dropped.
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?([^\n]*)\n(?:.*?\n)?\1\b", re.S)

TEMP_TOKEN = (
    r"(?:"
    r"/tmp/|/var/tmp/|"
    r"\$(?:TMPDIR|TEMP|TMP)\b|\$\{(?:TMPDIR|TEMP|TMP)\}?"
    r"|\$env:(?:TEMP|TMP)\b|%TEMP%|%TMP%|"
    r"AppData[/\\]+Local[/\\]+Temp[/\\]"
    r")"
)

SCRIPT_ON_TEMP = re.compile(
    TEMP_TOKEN + r"[^\s'\";|&<>]*\.(?:py|sh|ps1|js|mjs|ts|bat|cmd)\b",
    re.I,
)
REST = r"[^\s'\";|&<>]*"
REDIR_TO_TEMP = re.compile(r">{1,2}\s*['\"]?" + TEMP_TOKEN + REST, re.I)
TEE_TO_TEMP = re.compile(r"\btee\b[^\n;|&]*?" + TEMP_TOKEN + REST, re.I)
SCRATCHPAD = re.compile(r"[/\\]scratchpad[/\\]", re.I)


def hits(s: str) -> bool:
    """True when a temp path outside the session scratchpad is written to or run."""
    for pat in (SCRIPT_ON_TEMP, REDIR_TO_TEMP, TEE_TO_TEMP):
        for m in pat.finditer(s):
            if not SCRATCHPAD.search(m.group(0)):
                return True
    return False


def check(cmd: str) -> str | None:
    s = HEREDOC.sub(lambda m: m.group(2), cmd)
    if hits(s):
        return (
            "CHẶN: không tạo hoặc chạy script/file tạm trong $TEMP hay /tmp.\n"
            "  File ở vùng tạm biến mất sau phiên — Aurel không đọc lại được script đã chạy.\n"
            "  Cách đúng:\n"
            "    - Việc lặp lại > 1 lần: viết hẳn thành tool trong `01_Origine/04_Tools/VaultTool/`.\n"
            "    - Script nháp 1 lần: đặt trong thư mục scratchpad của phiên.\n"
            "    - Kiểm tra ngắn 1 lần: chạy `python -c \"...\"` trực tiếp trên dòng lệnh."
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
