#!/usr/bin/env python3
"""Unit tests for chan_sua_rao_chan.py (plugin-benchmark-20261124 G6).

Expected result: 0 = allow; "ask" = Claude Code payload answered with `permissionDecision: "ask"`.
Each "ask" case is replayed as a non-Claude payload, where it must block (2).
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

HOOK = Path(__file__).with_name("chan_sua_rao_chan.py")
VAULT = "D:\\AureLysn"
PLUGIN = "D:\\AureLysn\\01_Origine\\03_Systems\\Plugin"
FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

CASES = [
    # (tool, file path or command, cwd, expected, description)
    ("Write", "D:\\AureLysn\\CLAUDE.md", VAULT, "ask", "Write CLAUDE.md của vault"),
    ("Edit", "D:\\AureLysn-wt\\x\\CLAUDE.md", VAULT, "ask", "Edit CLAUDE.md trong worktree"),
    ("Edit", PLUGIN + "\\git-guard\\hooks\\hooks.json", VAULT, "ask", "Edit hooks.json"),
    ("Edit", PLUGIN + "\\git-guard\\.claude-plugin\\plugin.json", VAULT, "ask", "Edit plugin.json"),
    ("MultiEdit", PLUGIN + "\\.claude-plugin\\marketplace.json", VAULT, "ask", "MultiEdit marketplace.json"),
    ("Write", "C:\\Users\\x\\.claude\\settings.json", VAULT, "ask", "Write settings.json người dùng"),
    ("Edit", "D:\\AureLysn\\.claude\\settings.local.json", VAULT, "ask", "Edit settings.local.json của dự án"),
    ("Edit", "C:\\Users\\x\\.claude\\plugins\\cache\\aurelysn-vault\\git-guard\\0.8.0\\hooks\\chan_git_mv.py",
     VAULT, "ask", "Edit hook đã cài"),
    ("Write", "C:\\Users\\x\\.claude.json", VAULT, "ask", "Write ~/.claude.json"),
    ("Edit", "CLAUDE.md", VAULT, "ask", "đường dẫn tương đối"),
    ("Write", "D:\\AureLysn\\01_Origine\\05_Meta\\Rules\\hook\\no-x.md", VAULT, "ask", "Write luật hook của vault"),
    ("Edit", "D:\\AureLysn-wt\\x\\01_Origine\\05_Meta\\Rules\\hook\\no-x.md", VAULT, "ask", "Edit luật hook trong worktree"),
    ("Edit", "D:\\AureLysn\\01_Origine\\05_Meta\\Rules\\global\\principles.md", VAULT, 0, "note luật khác"),
    ("Edit", PLUGIN + "\\git-guard\\hooks\\chan_git_mv.py", VAULT, 0, "script hook trong bản vault (qua PR)"),
    ("Edit", "D:\\AureLysn\\_VAULT-MOC.md", VAULT, 0, "note thường"),
    ("Edit", "D:\\AureLysn\\.vscode\\settings.json", VAULT, 0, "settings.json ngoài .claude"),
    ("Write", "C:\\Users\\x\\.claude\\projects\\D--AureLysn\\memory\\MEMORY.md", VAULT, 0, "memory của phiên"),
    # shell
    ("Bash", "echo x > CLAUDE.md", VAULT, "ask", "chuyển hướng vào CLAUDE.md"),
    ("Bash", "echo x >> D:/AureLysn/01_Origine/03_Systems/Plugin/git-guard/hooks/hooks.json", VAULT, "ask", "nối vào hooks.json"),
    ("Bash", "cp new.json ~/.claude/settings.json", VAULT, "ask", "cp đè settings.json"),
    ("PowerShell", 'Set-Content -Path "C:\\Users\\x\\.claude\\settings.json" -Value "{}"', VAULT, "ask",
     "Set-Content settings.json"),
    ("PowerShell", "Remove-Item D:\\AureLysn\\CLAUDE.md", VAULT, "ask", "xoá CLAUDE.md"),
    ("Bash", 'bash -c "echo {} > .claude/settings.local.json"', VAULT, "ask", "bọc trong bash -c"),
    ("Bash", "cat <<'EOF' > CLAUDE.md\nnội dung mới\nEOF", VAULT, "ask", "heredoc ghi đè CLAUDE.md"),
    ("Bash", "cd /d/AureLysn && rm 01_Origine/05_Meta/Rules/hook/no-x.md", "C:\\x", "ask", "xoá luật hook"),
    ("Bash", "echo x > D:/AureLysn/bàn-giao/CLAUDE.md", VAULT, "ask", "đường dẫn có chữ à, payload UTF-8"),
    ("Edit", "D:\\AureLysn\\hoàn tất\\CLAUDE.md", VAULT, "ask", "đường dẫn file tiếng Việt"),
    ("Write", "D:\\AureLysn\\$id\\CLAUDE.md", VAULT, "ask", "$ trong đường dẫn của công cụ file là chữ"),
    ("PowerShell", "git commit -m @'\ndon't; echo x > CLAUDE.md\n'@", VAULT, 0, "here-string có dấu nháy"),
    ("Bash", "for f in a b; do echo x > CLAUDE.md; done", VAULT, "ask", "ghi trong vòng lặp một dòng"),
    ("Bash", "cat CLAUDE.md", VAULT, 0, "đọc CLAUDE.md"),
    ("Bash", "grep -n PreToolUse git-guard/hooks/hooks.json", VAULT, 0, "grep hooks.json"),
    ("Bash", 'git commit -m "sửa CLAUDE.md và hooks.json"', VAULT, 0, "chỉ nhắc trong commit message"),
    ("Bash", "python x.py > out.txt 2>&1", VAULT, 0, "chuyển hướng ra file thường"),
    ("Bash", "echo x > CLAUDE.md.bak", VAULT, 0, "tên khác CLAUDE.md"),
    ("Bash", 'echo "a > CLAUDE.md"', VAULT, 0, "dấu > nằm trong chuỗi"),
    ("PowerShell", "Get-Content C:\\Users\\x\\.claude\\settings.json", VAULT, 0, "Get-Content settings.json"),
]


def payload(tool: str, target: str, cwd: str, claude: bool) -> str:
    key = "file_path" if tool in FILE_TOOLS else ("command" if claude else "CommandLine")
    if claude:
        return json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": cwd, "tool_input": {key: target}},
                          ensure_ascii=False)
    name = tool if tool in FILE_TOOLS else "run_command"
    return json.dumps({"toolName": name, "cwd": cwd, "toolInput": {key: target}}, ensure_ascii=False)


def result(tool: str, target: str, cwd: str, claude: bool) -> object:
    r = subprocess.run([sys.executable, str(HOOK)], input=payload(tool, target, cwd, claude),
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 0 and r.stdout.strip():
        try:
            return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"]
        except Exception:
            return "bad-json"
    return r.returncode


def main() -> int:
    failed = total = 0
    for tool, target, cwd, want, desc in CASES:
        checks = [(True, want)] + ([(False, 2)] if want == "ask" else [])
        for claude, exp in checks:
            total += 1
            got = result(tool, target, cwd, claude)
            ok = got == exp
            failed += not ok
            host = "claude" if claude else "khác  "
            print(f"  [{'OK  ' if ok else 'FAIL'}] {host} ({got}=={exp}) {tool}: {desc}")
    print(f"\n{total - failed}/{total} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
