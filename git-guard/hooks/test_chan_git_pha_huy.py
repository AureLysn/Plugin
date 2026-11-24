#!/usr/bin/env python3
"""Unit tests for chan_git_pha_huy.py.

Expected result per case:
  0     = allow (exit 0, no decision printed)
  2     = hard block (exit 2)
  "ask" = Claude Code payload: exit 0 with `permissionDecision: "ask"` on stdout
Each "ask" case is also replayed as a non-Claude payload (Antigravity keys), where it must block (2).
The `git worktree remove` cases use a scratch folder with a fake nested checkout (a `.git` file).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    # work kept outside the branch (plugin-benchmark-20261124 N2; allowed until 0.8.0)
    ("git stash drop", "ask", "stash drop"),
    ("git stash drop stash@{1}", "ask", "stash drop có chỉ số"),
    ("git stash clear", "ask", "stash clear"),
    ("git stash", 0, "stash (cất tạm) được phép"),
    ("git stash pop", 0, "stash pop được phép"),
    ("git stash list", 0, "stash list được phép"),
    ("git worktree remove --force ../wt", "ask", "worktree remove --force"),
    ("git worktree remove -f ../wt", "ask", "worktree remove -f"),
    ("git -C D:/AureLysn worktree remove --force D:/AureLysn-wt/x", "ask", "git -C … worktree remove --force"),
    ("git worktree remove D:/AureLysn-wt/x", 0, "worktree remove (không --force) được phép"),
    ("git worktree prune", 0, "worktree prune được phép"),
    ('bash -c "git stash clear"', "ask", "stash clear bọc trong bash -c"),
    ("Set-Location D:/AureLysn; git reset --hard", "ask", "PowerShell ; reset --hard"),
    # wrapped or launched through another program (plugin-benchmark-20261124 N1; allowed until 0.8.0)
    ('bash -c "git reset --hard"', "ask", "bọc trong bash -c"),
    ('powershell -Command "git add -A"', 2, "bọc trong powershell -Command"),
    ("pwsh -c 'git push --force origin main'", "ask", "bọc trong pwsh -c"),
    ("cmd /c git clean -fdx", "ask", "bọc trong cmd /c"),
    ('& "C:\\Program Files\\Git\\cmd\\git.exe" reset --hard', "ask", "toán tử & với đường dẫn git.exe"),
    ("Start-Process git -ArgumentList 'reset','--hard' -Wait", "ask", "Start-Process -ArgumentList"),
    ("time git branch -D old", "ask", "tiền tố time"),
    ("bash <<'EOF'\ngit reset --hard\nEOF", "ask", "heredoc đưa vào bash"),
    ("echo $(git add -A)", 2, "trong $( )"),
    ("if ($true) { git add -A }", 2, "trong khối if của PowerShell"),
    ("(cd D:/AureLysn-wt/x && git push --force)", "ask", "trong subshell ( )"),
    # found by the review of V2 (plugin-benchmark-20261124 N7); allowed until 0.8.0
    ("for r in a b; do git -C $r reset --hard; done", "ask", "trong vòng lặp một dòng"),
    ("if [ -d x ]; then git add -A; fi", 2, "sau then"),
    ("git push \\\n  --force", "ask", "nối dòng bằng \\"),
    ("cmd //c \"git reset --hard\"", "ask", "cmd //c của Git Bash"),
    ('eval "git add -A"', 2, "eval"),
    ("cat <<EOF | bash\ngit reset --hard\nEOF", "ask", "heredoc qua ống vào bash"),
    # mentions only, not commands
    ("git status # rồi git add -A; git reset --hard", 0, "chú thích"),
    ('git commit -m "dòng 1\ngit add -A\ngit reset --hard"', 0, "chuỗi nhiều dòng"),
    ("git commit -m 'don'\\''t; git add -A'", 0, "'\\'' của Bash"),
    ('git commit -m "không dùng git reset --hard hay git add -A"', 0, "nhắc trong commit message"),
    ("cat <<'EOF' > a.md\ngit push --force\nEOF", 0, "nhắc trong heredoc"),
    ("echo git add -A", 0, "echo không phải lệnh git"),
    ("git log --oneline -5", 0, "lệnh đọc được phép"),
    ('git commit -m "đừng chạy bash -c \'git reset --hard\'"', 0, "bash -c chỉ nhắc trong commit message"),
    ("cat <<'EOF' > a.md\npowershell -Command \"git add -A\"\nEOF", 0, "wrapper nằm trong heredoc của cat"),
    ("git commit -m 'giữ nguyên $(git add -A)'", 0, "$( ) trong ngoặc đơn là chữ"),
]


def nested_cases(tmp: Path) -> list[tuple[str, object, str]]:
    """`git worktree remove` of a worktree that holds nested checkouts (V9; allowed until 0.8.0)."""
    root = tmp.as_posix()
    for d in ("wt/04_Portfolio", "wt/05_Evasion", "plain/01_Origine"):
        (tmp / d).mkdir(parents=True)
    (tmp / "wt/04_Portfolio/.git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    (tmp / "wt/05_Evasion/.git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    win = str(tmp / "wt")
    return [
        (f"git worktree remove {root}/wt", "ask", "worktree còn checkout lồng"),
        (f'git worktree remove "{win}"', "ask", "đường dẫn Windows trong ngoặc"),
        (f'git -C "{root}" worktree remove wt', "ask", "git -C <gốc> worktree remove tương đối"),
        (f'cd "{root}" && git worktree remove wt', "ask", "cd rồi worktree remove tương đối"),
        (f'Set-Location "{win}\\.."; git worktree remove wt', "ask", "PowerShell Set-Location rồi remove"),
        (f'$wt = "{win}"; git worktree remove $wt', "ask", "đường dẫn trong biến PowerShell"),
        (f'bash -c "git worktree remove {root}/wt"', "ask", "bọc trong bash -c"),
        (f"git worktree remove {root}/wt/04_Portfolio", 0, "gỡ chính checkout lồng được phép"),
        (f"git worktree remove {root}/plain", 0, "worktree không có checkout lồng được phép"),
        (f"git worktree remove {root}/khong-co", 0, "thư mục không tồn tại: để git tự báo"),
        (f"echo git worktree remove {root}/wt", 0, "echo không phải lệnh git"),
        (f"git worktree list {root}/wt", 0, "worktree list được phép"),
    ]


def run(cmd: str, claude: bool) -> tuple[int, str]:
    if claude:
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": cmd}}
    else:
        payload = {"toolName": "run_command", "toolInput": {"CommandLine": cmd}}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload, ensure_ascii=False),
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
    tmp = Path(tempfile.mkdtemp(prefix="test_git_pha_huy_"))
    try:
        failed, total = run_cases(CASES + nested_cases(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{total - failed}/{total} ca đúng.")
    return 2 if failed else 0


def run_cases(cases: list) -> tuple[int, int]:
    failed = total = 0
    for cmd, want, desc in cases:
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
    return failed, total


if __name__ == "__main__":
    raise SystemExit(main())
