#!/usr/bin/env python3
"""Unit tests for chan_checkout_cay_chinh.py (`0` = allow, `2` = block)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("chan_checkout_cay_chinh.py")

CASES = [
    ("git checkout -b feat/test", "D:\\AureLysn", 2, "checkout -b trên cây chính D:\\AureLysn"),
    ("git checkout -b feat/test", "D:\\AureLysnOS\\01_Vault", 2, "checkout -b trên cây chính cũ"),
    ("git switch main", "/d/AureLysn", 2, "git switch trên đường dẫn MSYS /d/AureLysn"),
    ("gh pr checkout 42", "D:\\AureLysn", 2, "gh pr checkout trên cây chính"),
    ("git -C D:/AureLysn checkout feat/x", "D:\\Other", 2, "git -C trỏ vào cây chính"),
    ("cd D:/AureLysn && git checkout feat/x", "D:\\Other", 2, "cd vào cây chính rồi checkout"),
    ("git checkout -- AGENTS.md", "D:\\AureLysn", 0, "khôi phục 1 file có -- được phép"),
    ("git checkout HEAD -- 01_Origine/a.md", "D:\\AureLysn", 0, "checkout HEAD -- file được phép"),
    ("git checkout -b feat/test", "D:\\AureLysn-wt\\test", 0, "checkout trong worktree ngoài được phép"),
    ("cd D:/AureLysn-wt/test && git checkout -b feat/x", "D:\\AureLysn", 0, "cd sang worktree rồi checkout được phép"),
    ('git commit -m "không chạy git checkout main"', "D:\\AureLysn", 0, "nhắc trong commit message"),
]


def run(cmd: str, cwd: str) -> int:
    payload = json.dumps({
        "tool_name": "Bash",
        "cwd": cwd,
        "tool_input": {"command": cmd},
    })
    r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode


def main() -> int:
    failed = 0
    for cmd, cwd, want, desc in CASES:
        got = run(cmd, cwd)
        ok = got == want
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}=={want}) {desc}")
    print(f"\n{len(CASES) - failed}/{len(CASES)} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
