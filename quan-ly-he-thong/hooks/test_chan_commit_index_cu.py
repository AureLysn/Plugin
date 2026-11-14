#!/usr/bin/env python3
"""Unit tests for chan_commit_index_cu.py (`0` = allow, `2` = block)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).with_name("chan_commit_index_cu.py")


def make_fake_vault(tmp: Path, check_exit: int) -> Path:
    vault = tmp / "vault"
    script_dir = vault / "01_Origine/04_Tools/VaultTool/Core"
    script_dir.mkdir(parents=True)
    (vault / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (script_dir / "vault_index.py").write_text(
        f"import sys\nprint('mock vault_index --check exit {check_exit}')\nsys.exit({check_exit})\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=str(vault), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(vault), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(vault), check=True)
    subprocess.run(["git", "add", "AGENTS.md"], cwd=str(vault), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(vault), check=True)
    return vault


def run_hook(cmd: str, cwd: Path) -> int:
    payload = json.dumps({
        "tool_name": "Bash",
        "cwd": str(cwd),
        "tool_input": {"command": cmd},
    })
    r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test_chan_idx_"))
    failed = 0
    try:
        # Case 1: staged .md + stale index (exit 2) -> block (2)
        v_stale = make_fake_vault(tmp / "c1", check_exit=2)
        (v_stale / "note.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "note.md"], cwd=str(v_stale), check=True)
        got = run_hook('git commit -m "update note"', v_stale)
        ok = got == 2
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}==2) chặn khi có .md staged và index cũ")

        # Case 2: staged .md + fresh index (exit 0) -> allow (0)
        v_fresh = make_fake_vault(tmp / "c2", check_exit=0)
        (v_fresh / "note.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "note.md"], cwd=str(v_fresh), check=True)
        got = run_hook('git commit -m "update note"', v_fresh)
        ok = got == 0
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}==0) cho qua khi index khớp")

        # Case 3: only .py staged (no .md or index.json) -> allow (0) even if index check would fail
        v_py = make_fake_vault(tmp / "c3", check_exit=2)
        (v_py / "tool.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "tool.py"], cwd=str(v_py), check=True)
        got = run_hook('git commit -m "update tool"', v_py)
        ok = got == 0
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}==0) chỉ sửa .py thì không gọi check")

        # Case 4: non-vault repo -> allow (0)
        other = tmp / "other"
        other.mkdir()
        got = run_hook('git commit -m "msg"', other)
        ok = got == 0
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}==0) repo ngoài vault được phép")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{4 - failed}/4 ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
