#!/usr/bin/env python3
"""Unit tests for chan_git_pha_huy.py.

Expected result per case:
  0     = allow (exit 0, no decision printed)
  2     = hard block (exit 2)
  "ask" = Claude Code payload: exit 0 with `permissionDecision: "ask"` on stdout
Each "ask" case is also replayed as a non-Claude payload (Antigravity keys), where it must block (2).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("chan_git_pha_huy.py")

CASES = [
    # git add: blanket staging is a hard block
    ("git add -A", 2, "git add -A"),
    ("git add --all", 2, "git add --all"),
    ("git add .", 2, "git add ."),
    ("git add ./", 2, "git add ./"),
    ("git add :/", 2, "git add :/ (gốc repo)"),
    ("git add *", 2, "git add * (wildcard)"),
    ("git add -Av", 2, "cờ gộp -Av"),
    ("git -C D:/AureLysn-wt/x add -A", 2, "git -C ... add -A"),
    ("git status; git add -A && git commit -m x", 2, "add -A ở đoạn giữa chuỗi lệnh"),
    ("git.exe add .", 2, "git.exe trong PowerShell"),
    ("git add 01_Origine/a.md 01_Origine/b.md", 0, "stage file cụ thể được phép"),
    ("git add -- CLAUDE.md", 0, "add -- file cụ thể được phép"),
    # destructive commands: ask Aurel (Claude Code) / block (other hosts)
    ("git reset --hard", "ask", "reset --hard"),
    ("git reset --hard origin/main", "ask", "reset --hard có đích"),
    ("git reset --soft HEAD~1", 0, "reset --soft được phép"),
    ("git reset HEAD CLAUDE.md", 0, "bỏ stage 1 file được phép"),
    ("git checkout -- .", "ask", "checkout -- ."),
    ("git checkout .", "ask", "checkout ."),
    ("git checkout -- CLAUDE.md", 0, "checkout -- file cụ thể được phép"),
    ("git restore .", "ask", "restore ."),
    ("git restore --worktree --staged .", "ask", "restore --worktree ."),
    ("git restore --staged .", 0, "restore --staged . chỉ bỏ stage"),
    ("git restore CLAUDE.md", 0, "restore file cụ thể được phép"),
    ("git clean -fd", "ask", "clean -fd"),
    ("git clean -xdf", "ask", "clean -xdf cờ gộp"),
    ("git clean --force", "ask", "clean --force"),
    ("git clean -n", 0, "clean -n (chạy thử) được phép"),
    ("git clean -nd", 0, "clean -nd (chạy thử) được phép"),
    ("git push --force", "ask", "push --force"),
    ("git push -f origin feat/x", "ask", "push -f"),
    ("git push --force-with-lease origin feat/x", "ask", "push --force-with-lease"),
    ("git push origin +feat/x", "ask", "push refspec +"),
    ("git push -u origin feat/x", 0, "push thường được phép"),
    ("git branch -D feat/x", "ask", "branch -D"),
    ("git branch --delete --force feat/x", "ask", "branch --delete --force"),
    ("git branch -d feat/x", 0, "branch -d (đã merge) được phép"),
    ("Set-Location D:/AureLysn; git reset --hard", "ask", "PowerShell ; reset --hard"),
    # mentions only, not commands
    ('git commit -m "không dùng git reset --hard hay git add -A"', 0, "nhắc trong commit message"),
    ("cat <<'EOF' > a.md\ngit push --force\nEOF", 0, "nhắc trong heredoc"),
    ("echo git add -A", 0, "echo không phải lệnh git"),
    ("git log --oneline -5", 0, "lệnh đọc được phép"),
]


def run(cmd: str, claude: bool) -> tuple[int, str]:
    if claude:
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": cmd}}
    else:
        payload = {"toolName": "run_command", "toolInput": {"CommandLine": cmd}}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


def result(cmd: str, claude: bool) -> object:
    code, out = run(cmd, claude)
    if code == 0 and out.strip():
        try:
            dec = json.loads(out)["hookSpecificOutput"]["permissionDecision"]
            return dec
        except Exception:
            return "bad-json"
    return code


def main() -> int:
    failed = total = 0
    for cmd, want, desc in CASES:
        checks = [(True, want)]
        if want == "ask":
            checks.append((False, 2))
        for claude, exp in checks:
            total += 1
            got = result(cmd, claude)
            ok = got == exp
            failed += not ok
            host = "claude" if claude else "khác  "
            print(f"  [{'OK  ' if ok else 'FAIL'}] {host} ({got}=={exp}) {desc}")
    print(f"\n{total - failed}/{total} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
