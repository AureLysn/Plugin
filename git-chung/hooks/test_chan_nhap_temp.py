#!/usr/bin/env python3
"""Unit tests for chan_nhap_temp.py (`0` = allow, `2` = block)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("chan_nhap_temp.py")

CASES = [
    ("python /tmp/fix.py", 2, "chạy script .py trong /tmp"),
    ("python3 $TEMP/migrate.py", 2, "chạy script trong $TEMP"),
    ("cat <<'EOF' > /tmp/run.py\nprint(1)\nEOF", 2, "heredoc ghi ra /tmp/run.py"),
    ("echo hi > $TMPDIR/out.txt", 2, "redirect ra $TMPDIR"),
    ("python C:/Users/aurel/AppData/Local/Temp/a.py", 2, "AppData/Local/Temp/*.py"),
    ("python /c/Users/aurel/scratchpad/test.py", 0, "scratchpad/*.py được phép"),
    ("python C:/Users/aurel/AppData/Local/Temp/claude/x/scratchpad/a.py", 0, "scratchpad của phiên nằm trong Temp được phép"),
    ("echo hi > C:/Users/aurel/AppData/Local/Temp/claude/x/scratchpad/out.txt", 0, "redirect vào scratchpad của phiên được phép"),
    ("python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py", 0, "chạy tool chính thức trong vault"),
    ('python -c "import sys; print(sys.version)"', 0, "python -c trực tiếp được phép"),
    ("ls /tmp", 0, "chỉ xem /tmp, không ghi và không chạy script"),
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
