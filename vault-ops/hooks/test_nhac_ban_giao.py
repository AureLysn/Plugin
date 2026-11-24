#!/usr/bin/env python3
"""Unit tests for nhac_ban_giao.py (SessionStart / PreCompact, plugin-benchmark-20261124 V1).

A fake vault (CLAUDE.md + 01_Origine/ + the handoff note) is one Git repository with one extra
worktree. Each case checks the exit code (always 0) and words the output must or must not hold.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOOK = Path(__file__).with_name("nhac_ban_giao.py")


def make_vault(tmp: Path) -> Path:
    vault = tmp / "vault"
    (vault / "01_Origine").mkdir(parents=True)
    (vault / "06_Station/01_Daily_Logs").mkdir(parents=True)
    (vault / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    (vault / "06_Station/01_Daily_Logs/session-handoff.md").write_text("# handoff\nNỘI-DUNG-RIÊNG\n", encoding="utf-8")
    for args in (["init", "-q", "-b", "main"], ["config", "user.email", "t@example.com"], ["config", "user.name", "T"],
                 ["add", "CLAUDE.md", "06_Station"], ["commit", "-q", "-m", "init"],
                 ["worktree", "add", "-q", str(tmp / "wt-x"), "-b", "fix/x"]):
        subprocess.run(["git", *args], cwd=str(vault), check=True, capture_output=True)
    (vault / "dirty.md").write_text("x\n", encoding="utf-8")
    return vault


def run(payload: object) -> tuple[int, str]:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    r = subprocess.run([sys.executable, str(HOOK)], input=text, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test_nhac_ban_giao_"))
    results: list[tuple[str, bool]] = []
    try:
        vault = make_vault(tmp)
        code, out = run({"hook_event_name": "SessionStart", "source": "startup", "cwd": str(vault)})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"] if out.strip() else ""
        results.append(("SessionStart: exit 0 và có JSON additionalContext", code == 0 and bool(ctx)))
        results.append(("SessionStart: nêu nhánh main và số file chưa commit", "nhánh `main`" in ctx and "1 file chưa commit" in ctx))
        results.append(("SessionStart: nêu worktree khác", "wt-x" in ctx and "[fix/x]" in ctx))
        results.append(("SessionStart: trỏ tới session-handoff", "[[session-handoff]]" in ctx))
        results.append(("SessionStart: không chép nội dung note", "NỘI-DUNG-RIÊNG" not in ctx))
        results.append(("SessionStart startup: không có lời nhắc sau tóm tắt", "vừa được tóm tắt" not in ctx))

        results.append(("SessionStart: không có luật hook thì không nhắc luật", "Luật hook" not in ctx))
        rules = vault / "01_Origine/05_Meta/Rules/hook"
        rules.mkdir(parents=True)
        (rules / "luat-hong.md").write_text("---\ntype: rule\nstatus: active\n---\n\n# x\n", encoding="utf-8")
        code, out = run({"hook_event_name": "SessionStart", "source": "startup", "cwd": str(vault)})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"] if out.strip() else ""
        results.append(("SessionStart: nêu tên luật hook hỏng", "Luật hook có lỗi" in ctx and "`luat-hong`" in ctx))
        shutil.rmtree(rules)

        code, out = run({"hook_event_name": "SessionStart", "source": "compact", "cwd": str(vault / "01_Origine")})
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"] if out.strip() else ""
        results.append(("SessionStart compact: có lời nhắc đọc lại handoff", code == 0 and "vừa được tóm tắt" in ctx))

        code, out = run({"hook_event_name": "PreCompact", "trigger": "auto", "cwd": str(vault)})
        results.append(("PreCompact: exit 0, dặn giữ lại và nhắc ban-giao",
                        code == 0 and "giữ lại" in out and "`ban-giao`" in out and "nhánh `main`" in out))
        results.append(("PreCompact: không quá 1.500 ký tự", len(out.strip()) <= 1500))

        outside = tmp / "outside"
        outside.mkdir()
        code, out = run({"hook_event_name": "SessionStart", "source": "startup", "cwd": str(outside)})
        results.append(("ngoài vault: im lặng, exit 0", code == 0 and not out.strip()))

        code, out = run("{khong phai json")
        results.append(("JSON hỏng: im lặng, exit 0 (không bao giờ chặn)", code == 0 and not out.strip()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = 0
    for label, ok in results:
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] {label}")
    print(f"\n{len(results) - failed}/{len(results)} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
