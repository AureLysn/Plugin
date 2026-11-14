#!/usr/bin/env python3
"""PreToolUse hook (Bash): block `<cmd> | <filter>; echo $?` where the pipe masks the gate exit code.

When a verification gate (`vault_doctor.py`, `claim_check.py`, `chapter_gate.py`) is piped into
`tail`, `head`, `grep`, or `cat` without `set -o pipefail`, `$?` reports the filter's exit code (0)
instead of the gate's exit code (2).

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

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", re.S)
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
PIPEFAIL = re.compile(r"\bset\s+-o\s+pipefail\b|\bset\s+-[A-Za-z]*o\s+pipefail\b")

# A pipeline `| <cmd>` (not `||`) followed by `;` or newline and an inspection of `$?` (not `$PIPESTATUS`)
PIPE_THEN_STATUS = re.compile(
    r"(?<!\|)\|(?!\|)\s*[A-Za-z0-9_./-]+[^\n|]*?(?:;|\n)\s*"
    r"[^\n]*?(?<!PIPESTATUS)\$\?"
)


def check(cmd: str) -> str | None:
    s = QUOTED.sub('""', HEREDOC.sub("", cmd))
    if PIPEFAIL.search(s):
        return None
    if PIPE_THEN_STATUS.search(s):
        return (
            "CHẶN: đọc `$?` sau ống `|` sẽ lấy mã thoát của lệnh CUỐI ống (`tail`/`head`/`grep` = 0),\n"
            "  nuốt mất mã thoát 2 của cổng kiểm phía trước (pre-handoff-verification-checklist.md).\n"
            "  Cách đúng:\n"
            "    1. Chạy cổng trực tiếp KHÔNG qua ống `|` (Bash tự bắt mã thoát), HOẶC\n"
            "    2. Thêm `set -o pipefail;` ở đầu lệnh, HOẶC\n"
            "    3. Đọc `${PIPESTATUS[0]}` thay vì `$?`."
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
