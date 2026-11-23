#!/usr/bin/env python3
"""Unit tests for chan_git_mv.py (`0` = allow, `2` = block)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("chan_git_mv.py")

CASES = [
    ("git mv 01_Origine/a.md 01_Origine/b.md", 2, "git mv trực tiếp trên .md"),
    ("git -C D:/AureLysn mv old.md new.md", 2, "git -C ... mv .md"),
    ('git mv "note cu.md" "note moi.md"', 2, "git mv .md có ngoặc kép"),
    ("git status && git mv foo.MD bar.MD", 2, "git mv sau &&"),
    ("git mv script.py script2.py", 0, "git mv trên .py được phép"),
    ("git mv image.png image2.png", 0, "git mv trên ảnh được phép"),
    ('git commit -m "tránh dùng git mv foo.md"', 0, "nhắc trong commit message"),
    ("cat <<'EOF'\ngit mv a.md b.md\nEOF", 0, "nằm trong heredoc"),
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
