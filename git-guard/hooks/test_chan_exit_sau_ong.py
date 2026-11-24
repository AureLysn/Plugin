#!/usr/bin/env python3
"""Unit tests for chan_exit_sau_ong.py (`0` = allow, `2` = block)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOOK = Path(__file__).with_name("chan_exit_sau_ong.py")

CASES = [
    ("python vault_doctor.py | tail -5; echo $?", 2, "pipe sang tail rồi echo $?"),
    ("python claim_check.py | head -n 20; printf 'EXIT=%s\\n' $?", 2, "pipe sang head rồi in $?"),
    ("python vault_doctor.py | grep ERROR\necho $?", 2, "pipe rồi xuống dòng echo $?"),
    ("python vault_doctor.py; echo $?", 0, "không có ống | thì echo $? đúng"),
    ("set -o pipefail; python vault_doctor.py | tail -5; echo $?", 0, "có set -o pipefail"),
    ("python vault_doctor.py | tail -5; echo ${PIPESTATUS[0]}", 0, "dùng PIPESTATUS[0]"),
    ("python vault_doctor.py || echo $?", 0, "toán tử || không phải ống |"),
    ("python vault_doctor.py | tail -5", 0, "pipe để xem đầu ra, không đọc $? giả"),
    # wrapped (plugin-benchmark-20261124 G3; allowed until 0.8.0)
    ('bash -c "python vault_doctor.py | tail -5; echo $?"', 2, "bọc trong bash -c"),
    # PowerShell: `$?` is about the last pipeline, not the pipe (false block found by replaying
    # real commands, 2026-11-24); a sh command handed over from PowerShell is still checked
    ("git diff --cached --stat | Select-Object -Last 1; git commit -q -m x; if ($?) { git push }", 0,
     "PowerShell: $? sau git commit", "PowerShell"),
    ("bash -c 'python vault_doctor.py | tail -5; echo $?'", 2, "PowerShell gọi bash -c", "PowerShell"),
]


def run(cmd: str, tool: str = "Bash") -> int:
    payload = json.dumps({"tool_name": tool, "tool_input": {"command": cmd}})
    r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode


def main() -> int:
    failed = 0
    for cmd, want, desc, *tool in CASES:
        got = run(cmd, *tool)
        ok = got == want
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}=={want}) {desc}")
    print(f"\n{len(CASES) - failed}/{len(CASES)} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
