#!/usr/bin/env python3
"""The copies of tach_lenh.py and duong_dan.py in vault-ops must equal the git-guard originals,
byte for byte.

vault-ops cannot import across plugins (installed plugins sit in separate version folders), so
it carries copies. This test runs in the vault folder, where both plugins are side by side; in
an installed cache the originals are not there and the test says so and passes.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ORIGINALS = HERE.parents[1] / "git-guard" / "hooks"


def main() -> int:
    failed = 0
    for name in ("tach_lenh.py", "duong_dan.py"):
        original = ORIGINALS / name
        if not original.is_file():
            print(f"  [OK  ] không có bản gốc {original} (bản cài đặt): bỏ qua")
        elif (HERE / name).read_bytes() == original.read_bytes():
            print(f"  [OK  ] {name} của vault-ops giống hệt bản của git-guard")
        else:
            failed += 1
            print(f"  [FAIL] {name} của vault-ops khác bản của git-guard.\n"
                  f"         Sửa ở git-guard/hooks/{name} rồi chép đè:\n"
                  f"         cp git-guard/hooks/{name} vault-ops/hooks/{name}")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
