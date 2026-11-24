#!/usr/bin/env python3
"""Unit tests for chan_sed_i.py (`0` = allow, `2` = block)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOOK = Path(__file__).with_name("chan_sed_i.py")

CASES = [
    ("sed -i 's/a/b/g' file.md", 2, "sed -i cơ bản"),
    ("sed -i.bak 's/a/b/' file.md", 2, "sed -i.bak"),
    ("sed -Ei 's/a/b/' file.md", 2, "sed -Ei gộp cờ"),
    ("sed --in-place 's/a/b/' file.md", 2, "sed --in-place"),
    ("find . -name '*.md' | xargs sed -i 's/a/b/'", 2, "xargs sed -i sau ống"),
    ("sed 's/a/b/g' file.md", 0, "sed in ra stdout (không -i) được phép"),
    ("sed -n '1,20p' file.md", 0, "sed -n đọc dòng được phép"),
    ('git commit -m "cấm dùng sed -i trên Windows"', 0, "nhắc trong commit message"),
    ("cat <<'EOF'\nsed -i 's/a/b/' x\nEOF", 0, "nằm trong heredoc"),
    # wrapped (plugin-benchmark-20261124 G3; allowed until 0.8.0)
    ('bash -c "sed -i s/a/b/ file.md"', 2, "bọc trong bash -c"),
    ('git commit -m "đừng chạy bash -c \'sed -i x\'"', 0, "bash -c chỉ nhắc trong commit message"),
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
