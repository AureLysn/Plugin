#!/usr/bin/env python3
"""PreToolUse hook (Bash): block `<cmd> | <filter>; echo $?` where the pipe masks the gate exit code.

When a verification gate (`vault_doctor.py`, `claim_check.py`, `chapter_gate.py`) is piped into
`tail`, `head`, `grep`, or `cat` without `set -o pipefail`, `$?` reports the filter's exit code (0)
instead of the gate's exit code (2).

PowerShell commands are skipped unless they hand text to a sh-family shell: there `$?` after
`git … | Select-Object …; git commit …` is about `git commit`, not about the pipe, and
`$LASTEXITCODE` is not masked by one (a false block found by replaying real commands, 0.8.0).

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
SH_WORD = re.compile(r"\b(?:bash|sh|zsh|dash|wsl)\b", re.I)
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
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace"))
    except Exception:
        return unreadable("stdin không phải JSON")
    ti = (data.get("tool_input") or data.get("toolInput")) if isinstance(data, dict) else None
    if not isinstance(ti, dict):
        return unreadable("không có tool_input")
    cmd = ti.get("command") or ti.get("CommandLine") or ""
    if not isinstance(cmd, str):
        return unreadable("command không phải chuỗi")
    tool = str(data.get("tool_name") or data.get("toolName") or "").lower()
    if tool == "powershell" and not SH_WORD.search(cmd):
        return 0
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
