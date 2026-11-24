#!/usr/bin/env python3
"""Unit tests for tach_lenh.py.

A case with an expected string passes when one variant, read back (`decode`), contains it
(whitespace collapsed). A case with None passes when `variants` returns one form only: the text is
data, not a command. SHELL cases name the shell the text is typed in; EXACT cases give the
normalised text. Most SHELL cases come from the review of 2026-11-24 (V2).
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))
from tach_lenh import decode, normalise, variants  # noqa: E402

ENC = base64.b64encode("git add -A".encode("utf-16-le")).decode()

CASES = [
    # wrappers: the command they run must appear as a variant
    ('bash -c "git reset --hard"', "git reset --hard", "bash -c"),
    ("bash -lc 'git push -f'", "git push -f", "bash -lc (cờ gộp)"),
    ('sh -c "cd /d/AureLysn && git checkout main"', "cd /d/AureLysn && git checkout main", "sh -c giữ cd bên trong"),
    ('cd /d/AureLysn && bash -c "git checkout main"', "cd /d/AureLysn && git checkout main", "cd trước wrapper vẫn còn"),
    ('powershell -Command "git add -A"', "git add -A", "powershell -Command"),
    ("powershell -NoProfile -ExecutionPolicy Bypass -Command git add -A", "git add -A", "tham số trước -Command"),
    ("pwsh -c 'git push --force origin main'", "git push --force origin main", "pwsh -c"),
    ('powershell "git add -A"', "git add -A", "script ở vị trí đầu tiên"),
    ("powershell -Command { git reset --hard }", "git reset --hard", "script block"),
    ('powershell -Command "& {git reset --hard}"', "git reset --hard", "& { } trong -Command"),
    (f"powershell -EncodedCommand {ENC}", "git add -A", "-EncodedCommand"),
    ("cmd /c git clean -fdx", "git clean -fdx", "cmd /c không ngoặc"),
    ('cmd.exe /C "git checkout main"', "git checkout main", "cmd.exe /C có ngoặc"),
    ("iex 'git clean -fd'", "git clean -fd", "iex"),
    ("Start-Process git -ArgumentList 'reset','--hard' -Wait", "git reset --hard", "Start-Process danh sách"),
    ("Start-Process git -ArgumentList 'reset', '--hard'", "git reset --hard", "Start-Process danh sách có cách"),
    ('Start-Process -FilePath git -ArgumentList "push --force"', "git push --force", "Start-Process -FilePath"),
    ("pwsh -c \"bash -c 'git add -A'\"", "git add -A", "lồng hai tầng"),
    # launchers and the git program itself
    ('& "C:\\Program Files\\Git\\cmd\\git.exe" reset --hard', "git reset --hard", "& với đường dẫn có ngoặc"),
    ('"C:\\Program Files\\Git\\cmd\\git.exe" mv a.md b.md', "git mv a.md b.md", "đường dẫn git có ngoặc"),
    ("git.exe mv a.md b.md", "git mv a.md b.md", "git.exe"),
    ("time git branch -D old", "git branch -D old", "tiền tố time"),
    ("env GIT_TRACE=1 git push -f", "git push -f", "env VAR="),
    ("nohup git reset --hard &", "git reset --hard", "nohup"),
    ("timeout 30 git clean -fd", "git clean -fd", "timeout có thời lượng"),
    # bodies run by a shell
    ("bash <<'EOF'\ngit reset --hard\nEOF", "git reset --hard", "heredoc đưa vào bash"),
    ('bash <<< "git add -A"', "git add -A", "here-string"),
    ("echo $(git reset --hard)", "git reset --hard", "$( )"),
    ("echo `git add -A`", "git add -A", "backtick"),
    ("if (Test-Path x) { git reset --hard }", "git reset --hard", "thân khối if của PowerShell"),
    ("Get-ChildItem | ForEach-Object { git add -A }", "git add -A", "thân ForEach-Object"),
    ("(cd /d/AureLysn && git checkout main)", "cd /d/AureLysn && git checkout main", "subshell ( )"),
    # data, not commands: nothing beyond the command itself
    ('git commit -m "bash -c \'git reset --hard\'"', None, "bash -c chỉ nằm trong commit message"),
    ('echo "powershell -Command \\"git add -A\\""', None, "tham số của echo"),
    ("cat <<'EOF' > a.md\nbash -c \"git push --force\"\nEOF", None, "heredoc đưa vào cat"),
    ("git commit -m 'literal $(git reset --hard)'", None, "$( ) trong ngoặc đơn"),
    ('python -c "print(\'git add -A\')"', None, "python -c chưa được mở (giới hạn đã ghi)"),
    ("git log --oneline -5", None, "lệnh git thường"),
    ("Set-Location D:/AureLysn; git status", None, "PowerShell thường"),
    ("git stash drop stash@{1}", None, "stash@{1} không phải khối lệnh"),
    ("$h = @{ a = 1 }", None, "@{ } là hashtable"),
    ("find . -name x -exec rm {} +", None, "{} rỗng của find"),
    ("echo '(git add -A)'", None, "( ) trong ngoặc đơn là chữ"),
]


NL = "\n"

# (command, shell, text a variant must hold, text no variant may hold, description)
SHELL = [
    # comments
    ("git status # git add -A; git reset --hard", "bash", None, "git add", "chú thích cuối dòng"),
    ("# it's slow" + NL + "git add -A", "bash", "git add -A", None, "dấu nháy trong chú thích"),
    ("ls a#b; git add -A", "bash", "git add -A", None, "# giữa từ không phải chú thích"),
    ("echo ${#x}; git add -A", "bash", "git add -A", None, "${#x} không phải chú thích"),
    ("<# git add -A" + NL + "#>" + NL + "git status", "powershell", "git status", "git add", "chú thích khối PowerShell"),
    ("$a = 1 # git add -A", "powershell", None, "git add", "chú thích sau phép gán"),
    # here-strings
    ("git commit -m @'" + NL + "don't git add -A; git reset --hard" + NL + "'@", "powershell", None, "commit; git",
     "here-string có dấu nháy"),
    ("@'" + NL + "it's" + NL + "'@ | Set-Content a.md; git add -A", "powershell", "git add -A", None, "lệnh sau here-string"),
    ('gh pr create --body @"' + NL + 'a "b" $(git add -A)' + NL + '"@', "powershell", "git add -A", None,
     "$( ) trong here-string kép"),
    ("powershell -Command @'" + NL + "git add -A" + NL + "'@", "powershell", "git add -A", None, "here-string làm script"),
    # continued lines
    ("git reset \\" + NL + "  --hard", "bash", "git reset --hard", None, "nối dòng Bash"),
    ("git push `" + NL + "  --force", "powershell", "git push --force", None, "nối dòng PowerShell"),
    ("git add \\\r" + NL + "  -A", "bash", "git add -A", None, "nối dòng CRLF"),
    # quotes of each shell
    ('Get-ChildItem "D:\\AureLysn\\"; git add -A', "powershell", "git add -A", None, "chuỗi PowerShell kết thúc bằng \\"),
    ("$r = $p.Replace('\\', '/'); git add -A", "powershell", "git add -A", None, "'\\' của PowerShell"),
    ("git commit -m 'don'\\''t; git add -A'", "bash", None, "; git add", "'\\'' của Bash"),
    ("echo $'it\\'s; git add -A'", "bash", None, "; git add", "$'…' của Bash"),
    ('echo "a `date`"; git add -A', "bash", "git add -A", None, "backtick trước dấu nháy đóng"),
    ('Write-Output "a`n"; git add -A; Write-Output "b`n"', "powershell", "git add -A", None, "backtick của PowerShell không phải $( )"),
    ('git commit -m "dòng 1' + NL + 'git add -A"', "bash", None, NL + "git add", "chuỗi nhiều dòng"),
    ("cmd /c \"echo it's & git add -A\"", "powershell", "git add -A", None, "dấu nháy đơn trong cmd"),
    # bodies and keywords
    ("for r in a b; do git add -A; done", "bash", "a b;git add -A; done", None, "do trên một dòng"),
    ("if [ -f x ]; then git add -A; fi", "bash", "git add -A", None, "then trên một dòng"),
    ("while read f; do bash -c 'git add -A'; done < x", "bash", "git add -A", None, "wrapper sau do"),
    ("! git add -A", "bash", "git add -A", None, "! phủ định"),
    ("$out = @(git add -A 2>&1)", "powershell", "git add -A", None, "@( ) của PowerShell"),
    ("cmd //c \"git add -A\"", "bash", "git add -A", None, "cmd //c của Git Bash"),
    ('eval "git add -A"', "bash", "git add -A", None, "eval"),
    ("bash -c $'git add -A'", "bash", "git add -A", None, "bash -c $'…'"),
    ("uv run git add -A", "bash", "git add -A", None, "uv run"),
    ("try { if ($a) { if ($b) { if ($c) { git add -A } } } } catch { }", "powershell", "git add -A", None, "lồng bốn tầng"),
    ("; ".join(f"if ($x{i}) {{ ls f{i} }}" for i in range(20)) + "; if ($y) { git add -A }", "powershell", "git add -A", None,
     "khối thứ 21"),
    # heredocs
    ("cat <<-EOF > x" + NL + "\tdon't; git add -A" + NL + "\tEOF" + NL + "git status", "bash", "git status", "git add",
     "<<- với dấu đóng thụt vào"),
    ("cat <<\\EOF" + NL + "git add -A" + NL + "EOF", "bash", None, "git add", "<<\\EOF"),
    ("cat <<EOF" + NL + "x $(git add -A)" + NL + "EOF", "bash", "git add -A", None, "$( ) trong heredoc không trích dẫn"),
    ("cat <<EOF | bash" + NL + "git add -A" + NL + "EOF", "bash", "git add -A", None, "cat <<EOF | bash"),
    ("git commit -m \"$(cat <<'EOF'" + NL + "it's; git add -A" + NL + "EOF" + NL + ")\"; git status", "bash", "git status",
     "; git add", "heredoc trong $( ) trong chuỗi"),
]

EXACT = [
    ("git  status", None, "git  status"),
    ('echo "a;b"', "bash", 'echo "a' + chr(0xE100 + ord(";")) + 'b"'),
    ("a \\" + NL + "   b", "bash", "a  b"),
    ("x=$(date) # y", "bash", "x=" + chr(0xE0FF) + " "),
    ('ls "D:\\dir\\"', "powershell", 'ls "D:\\dir/"'),
    ("a `" + NL + "   b", "powershell", "a  b"),
    ("sed s,#,x,g a && ls", "bash", "sed s,#,x,g a && ls"),
    ("@(1,# x" + NL + "2)", "powershell", "@(1," + NL + "2)"),
]


def norm(s: str) -> str:
    return " ".join(decode(s).split())


def main() -> int:
    failed = total = 0

    def report(ok: bool, desc: str, got: object) -> None:
        nonlocal failed, total
        total += 1
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] {desc}" + ("" if ok else f"\n         -> {got!r}"))

    for cmd, want, desc in CASES:
        got = variants(cmd)
        ok = len(got) == 1 if want is None else any(norm(want) in norm(v) for v in got)
        report(ok and (want is None or len(got) > 1), desc, got)
    for cmd, shell, want, never, desc in SHELL:
        got = variants(cmd, shell)
        ok = (want is None or any(norm(want) in norm(v) for v in got)) and \
            (never is None or not any(never in v for v in got))
        report(ok, f"{shell}: {desc}", got)
    for cmd, shell, want in EXACT:
        got = normalise(cmd, shell).text
        report(got == want, f"dạng chuẩn của {cmd!r}", got)
    many = "; ".join(f"if ($x{i}) {{ ls f{i} }}" for i in range(20)) + "; if ($y) { git add -A }"
    report("git add -A" in [norm(v) for v in variants(many, "powershell")], "thân của khối thứ 21 là một dạng riêng", "")
    big = "echo a; " * 20_000
    report(len(variants(big)) >= 1, "lệnh 160 KB không lỗi", "")
    print(f"\n{total - failed}/{total} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
