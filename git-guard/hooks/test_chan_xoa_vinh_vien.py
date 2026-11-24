#!/usr/bin/env python3
"""Unit tests for chan_xoa_vinh_vien.py (plugin-benchmark-20261124 N4).

Expected result: 0 = allow; "ask" = Claude Code payload answered with `permissionDecision: "ask"`.
Each "ask" case is replayed as a non-Claude payload (Antigravity keys), where it must block (2).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOOK = Path(__file__).with_name("chan_xoa_vinh_vien.py")
VAULT = "D:\\AureLysn"
WT = "D:\\AureLysn-wt\\x"
HOME = "C:\\Users\\x"
SP = "C:/Users/x/AppData/Local/Temp/claude/x/scratchpad"

CASES = [
    # (command, tool, cwd, expected, description)
    ("rm -rf D:/AureLysn/01_Origine/x", "Bash", HOME, "ask", "rm -rf trong vault"),
    ("rm D:/AureLysn/06_Station/00_Inbox/a.md", "Bash", HOME, "ask", "rm một note trong vault"),
    ("rm a.md", "Bash", VAULT, "ask", "rm đường dẫn tương đối khi đứng trong vault"),
    ("rm -rf build", "Bash", WT, "ask", "rm -rf trong worktree"),
    ("Remove-Item -Recurse -Force D:\\AureLysn\\02_Storage\\x", "PowerShell", HOME, "ask", "Remove-Item -Recurse trong kho"),
    ("Remove-Item 'G:\\My Drive\\AureLysn\\Storage\\00_Inbox\\a.png'", "PowerShell", HOME, "ask", "Remove-Item một file trên Drive"),
    ('cmd /c rd /s /q "D:\\AureLysn\\03_Atelier\\x"', "Bash", HOME, "ask", "cmd rd /s"),
    ("cmd /c del /s /q D:\\AureLysn\\03_Atelier\\*.tmp", "Bash", HOME, "ask", "cmd del /s"),
    ("rm -rf /c/Users/x/Desktop/old", "Bash", HOME, "ask", "rm -rf ngoài vault, ngoài vùng nháp"),
    ("rm -rf D:/", "Bash", HOME, "ask", "rm -rf cả ổ chứa vault"),
    ("cd /d/AureLysn && rm -rf tmp", "Bash", HOME, "ask", "cd vào vault rồi rm -rf"),
    ('bash -c "rm -rf D:/AureLysn/x"', "Bash", HOME, "ask", "bọc trong bash -c"),
    ("find D:/AureLysn/06_Station -name '*.tmp' -delete", "Bash", HOME, "ask", "find -delete trong vault"),
    ("find . -name '*.bak' -exec rm {} +", "Bash", VAULT, "ask", "find -exec rm trong vault"),
    ('robocopy D:\\AureLysn "G:\\My Drive\\AureLysn\\Mirror" /MIR', "PowerShell", HOME, "ask", "robocopy /MIR vào kho"),
    ('[System.IO.Directory]::Delete("D:\\AureLysn\\x", $true)', "PowerShell", HOME, "ask", ".NET Directory.Delete"),
    ('rm -rf "$UNKNOWN_DIR"', "Bash", HOME, "ask", "rm -rf đích chưa rõ"),
    ("rm $f", "Bash", VAULT, "ask", "rm đích chưa rõ khi đứng trong vault"),
    ("$r = Remove-Item -Recurse D:\\AureLysn\\x", "PowerShell", HOME, "ask", "Remove-Item trong phép gán"),
    ("if (Test-Path D:\\AureLysn\\x) { Remove-Item -Recurse D:\\AureLysn\\x }", "PowerShell", HOME, "ask",
     "Remove-Item trong khối if"),
    ("(cd /d/AureLysn && rm -rf tmp)", "Bash", HOME, "ask", "rm -rf trong subshell"),
    # found by replaying real commands (2026-11-24): `cd /d/…` was read as the cmd switch `/d`
    ("cd /d/AureLysn && rm a.md", "Bash", HOME, "ask", "cd /d/... của Git Bash rồi rm một note"),
    ("cd /d/AureLysn-wt/x; Remove-Item a.md", "PowerShell", HOME, "ask", "cd /d/... vào worktree rồi Remove-Item"),
    ('cmd /c "cd /d D:\\AureLysn && del a.md"', "Bash", HOME, "ask", "cd /d D:\\ của cmd rồi del"),
    ("for f in a b; do rm /d/AureLysn/$f.md; done", "Bash", HOME, 0, "đích chưa rõ, không đệ quy, ngoài vault"),
    ("for f in a b; do rm $f.md; done", "Bash", VAULT, "ask", "rm trong vòng lặp một dòng"),
    ("if [ -f a.md ]; then rm a.md; fi", "Bash", VAULT, "ask", "rm sau then"),
    ("rm -rf \\\n  D:/AureLysn/x", "Bash", HOME, "ask", "rm nối dòng"),
    ('cd "$(git rev-parse --show-toplevel)" && rm a.md', "Bash", VAULT, "ask", "cd chưa rõ trong phiên của vault"),
    ("git status # rm -rf D:/AureLysn", "Bash", HOME, 0, "chú thích"),
    ("git commit -m @'\ndon't; rm -rf D:/AureLysn\n'@", "PowerShell", VAULT, 0, "here-string có dấu nháy"),
    ('try { Push-Location C:\\t; Remove-Item a.txt } finally { Pop-Location }', "PowerShell", VAULT, 0, "cd trong khối try"),
    ("cd /d/AureLysn; if ($true) { Remove-Item a.md }", "PowerShell", HOME, "ask", "cd trước khối if, xoá trong khối"),
    ("Push-Location D:/AureLysn; git status; Pop-Location; Remove-Item a.md", "PowerShell", HOME + "\\Downloads", 0,
     "Pop-Location trả về thư mục cũ"),
    ("Get-ChildItem D:\\AureLysn\\x | ForEach-Object { Remove-Item $_.FullName -Recurse }", "PowerShell", HOME, "ask",
     "Remove-Item trong ForEach-Object, đích chưa rõ"),
    # allowed
    (f"rm -rf {SP}/bomtest", "Bash", HOME, 0, "rm -rf trong scratchpad"),
    ("rm -rf /tmp/x", "Bash", HOME, 0, "rm -rf trong /tmp"),
    ("rm -rf 01_Origine/04_Tools/VaultTool/__pycache__", "Bash", VAULT, 0, "xoá __pycache__"),
    ("rm -rf node_modules", "Bash", VAULT + "\\04_Portfolio\\Portfolio_Web", 0, "xoá node_modules"),
    ("rm notes.txt", "Bash", HOME + "\\Downloads", 0, "rm một file ngoài vault"),
    ("Remove-Item -Force old.log", "PowerShell", HOME, 0, "-Force không phải -Recurse"),
    (f'SP={SP}/t; rm -rf "$SP"', "Bash", HOME, 0, "biến gán trước trỏ vào scratchpad"),
    (f'$sp = "{SP}\\b"; Remove-Item -Recurse -Force $sp', "PowerShell", HOME, 0, "biến PowerShell trỏ vào scratchpad"),
    ("rm $f", "Bash", HOME + "\\Downloads", 0, "rm đích chưa rõ ngoài vault"),
    (f'$sp = "{SP}\\bomtest"; if (Test-Path $sp) {{ Remove-Item -Recurse -Force $sp -Confirm:$false }}', "PowerShell",
     VAULT, 0, "khối if dùng biến gán trước nó (ca thật 24/11)"),
    ("git rm -r old", "Bash", VAULT, 0, "git rm không thuộc hook này"),
    ('git commit -m "đừng rm -rf D:/AureLysn"', "Bash", VAULT, 0, "chỉ nhắc trong commit message"),
    ("echo rm -rf D:/AureLysn", "Bash", HOME, 0, "echo không xoá"),
    ("robocopy C:\\a C:\\b /E", "PowerShell", HOME, 0, "robocopy không có /MIR"),
    ("cat <<'EOF' > note.txt\nrm -rf D:/AureLysn\nEOF", "Bash", HOME, 0, "nằm trong heredoc"),
]


def run(cmd: str, tool: str, cwd: str, claude: bool) -> tuple[int, str]:
    if claude:
        payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": cwd, "tool_input": {"command": cmd}}
    else:
        payload = {"toolName": "run_command", "cwd": cwd, "toolInput": {"CommandLine": cmd}}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload, ensure_ascii=False),
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


def result(cmd: str, tool: str, cwd: str, claude: bool) -> object:
    code, out = run(cmd, tool, cwd, claude)
    if code == 0 and out.strip():
        try:
            return json.loads(out)["hookSpecificOutput"]["permissionDecision"]
        except Exception:
            return "bad-json"
    return code


def main() -> int:
    failed = total = 0
    for cmd, tool, cwd, want, desc in CASES:
        checks = [(True, want)] + ([(False, 2)] if want == "ask" else [])
        for claude, exp in checks:
            total += 1
            got = result(cmd, tool, cwd, claude)
            ok = got == exp
            failed += not ok
            host = "claude" if claude else "khác  "
            print(f"  [{'OK  ' if ok else 'FAIL'}] {host} ({got}=={exp}) {desc}")
    print(f"\n{total - failed}/{total} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
