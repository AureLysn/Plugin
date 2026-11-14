#!/usr/bin/env python3
"""Unit tests for chan_exit_sau_ong.py (`0` = allow, `2` = block)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
]


def run(cmd: str) -> int:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode


def main() -> int:
    failed = 0
    for cmd, want, desc in CASES:
        got = run(cmd)
        ok = got == want
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}=={want}) {desc}")
    print(f"\n{len(CASES) - failed}/{len(CASES)} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
