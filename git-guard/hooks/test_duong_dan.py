#!/usr/bin/env python3
"""Unit tests for duong_dan.py: working directory, variables, written files and `walk`.

Several cases come from replaying 932 real tool calls (2026-11-24): `cd /d/AureLysn` was read
as the cmd switch `/d`, and `if { }` bodies lost the variables and the `cd` before them.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from duong_dan import Scope, redirect_targets, walk, written_files  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VAULT = "D:\\AureLysn"

CD = [  # (commands stepped in order, start, expected cwd)
    (["cd /d/AureLysn"], "C:/x", "d:/aurelysn"),
    (["cd /d D:\\AureLysn"], "C:/x", "d:/aurelysn"),
    (["cd /d"], "C:/x", "d:/"),
    (["cd /c/Users/x"], VAULT, "c:/users/x"),
    (["cd /dev"], VAULT, "/dev"),
    (["pushd /d/AureLysn-wt/x"], "C:/x", "d:/aurelysn-wt/x"),
    (["Set-Location -LiteralPath D:/AureLysn/05_Evasion"], "C:/x", "d:/aurelysn/05_evasion"),
    (["Push-Location D:/AureLysn/05_Evasion", "Pop-Location"], VAULT, "d:/aurelysn"),
    (["pushd /d/AureLysn", "pushd 05_Evasion", "popd"], "C:/x", "d:/aurelysn"),
    (["popd"], VAULT, None),
    (["cd -"], VAULT, None),
    (["cd ../AureLysn-wt"], VAULT, "d:/aurelysn-wt"),
    (['cd "/d/AureLysn/06_Station/00_Inbox"'], "C:/x", "d:/aurelysn/06_station/00_inbox"),
]

REDIRECTS = [
    ("echo a > b.txt", ["b.txt"]),
    ("echo a >> 'b c.txt'", ["b c.txt"]),
    ("cmd 2>&1", []),
    ("cmd > /dev/null 2>&1", []),
    ('git commit -m "a > b"', []),
    ("cmd *> $null", []),
]

# (command, cwd, expected files written, in any order)
WRITTEN = [
    ("cd /d/AureLysn && echo x > CLAUDE.md", "C:/x", ["d:/aurelysn/claude.md"]),
    ("Copy-Item a.md,b.md D:/AureLysn/z", VAULT, ["d:/aurelysn/a.md", "d:/aurelysn/b.md", "d:/aurelysn/z"]),
    ("'x' | Set-Content D:/AureLysn/a.json", VAULT, ["d:/aurelysn/a.json"]),
    ("$p = 'D:/AureLysn/x'; if ($true) { 'a' > \"$p/y.md\" }", "C:/x", ["d:/aurelysn/x/y.md"]),
    ("cd /d/AureLysn; (cd 05_Evasion; rm note.md)", "C:/x", ["d:/aurelysn/05_evasion/note.md"]),
    ("cd /d/AureLysn && bash <<'EOF'\nrm note.md\nEOF", "C:/x", ["d:/aurelysn/note.md"]),
    ("cat D:/AureLysn/a.md | grep x", VAULT, []),
]


# files given new text only (`text_only=True`)
TEXT = [
    ("Set-Content D:/AureLysn/a.json -Value 'x.md'", VAULT, ["d:/aurelysn/a.json"]),
    ("Set-Content -Value 'x.md' -Path D:/AureLysn/a.json", VAULT, ["d:/aurelysn/a.json"]),
    ("Set-Content C:/t/a.txt 'b.md'", VAULT, ["c:/t/a.txt"]),
    ("'x' | Out-File -Encoding utf8 -Append D:/AureLysn/a.md", VAULT, ["d:/aurelysn/a.md"]),
    ("'x' | Out-File D:/AureLysn/a.md -Encoding utf8", VAULT, ["d:/aurelysn/a.md"]),
    ("Get-Content a.md | Tee-Object -FilePath:b.md", VAULT, ["d:/aurelysn/b.md"]),
    ("echo x | tee -a a.md b.md", VAULT, ["d:/aurelysn/a.md", "d:/aurelysn/b.md"]),
    ("Copy-Item a.md b.md 2>$null", VAULT, []),
    ("Remove-Item a.md", VAULT, []),
    ("python x.py > out.txt", VAULT, ["d:/aurelysn/out.txt"]),
]


# (command, shell, cwd, files given new text): review of 2026-11-24
SHELL_TEXT = [
    ('try { Push-Location C:/t; git diff > d.txt } finally { Pop-Location }', "powershell", VAULT, ["c:/t/d.txt"]),
    ('if (Test-Path C:/t) { Set-Location C:/t; python x.py > out.txt }', "powershell", VAULT, ["c:/t/out.txt"]),
    ('try { cd C:/t; if ($x) { "x" | Set-Content a.md } } catch {}', "powershell", VAULT, ["c:/t/a.md"]),
    ("cd (Join-Path $env:TEMP 'x'); git diff > d.txt", "powershell", VAULT, []),
    ('if ($x) { cd C:/t }; "x" > a.md', "powershell", VAULT, ["d:/aurelysn/a.md"]),
    ('Set-Content -Path "C:/t/a, b.md" -Value x', "powershell", VAULT, ["c:/t/a, b.md"]),
    ('Set-Content -Path C:/t/a.md,C:/t/b.md -Value x', "powershell", VAULT, ["c:/t/a.md", "c:/t/b.md"]),
    ('git diff > "${env:NO_SUCH_VAR_9x7}\\d.txt"', "powershell", VAULT, []),
    ('Set-Content -Path ("{0}\\a.md" -f $env:TEMP) -Value x', "powershell", VAULT, []),
    ('Set-Content -Path:"C:/t/a.md" -Value x', "powershell", VAULT, ["c:/t/a.md"]),
    ('Out-File -FilePath:"C:/t/a.md" -InputObject x', "powershell", VAULT, ["c:/t/a.md"]),
    ('"x" > "C:/t/a, b.md"', "powershell", VAULT, ["c:/t/a, b.md"]),
    ("git log | tee -Variable log.txt", "powershell", VAULT, []),
    ("git log | tee log.txt", "powershell", VAULT, ["d:/aurelysn/log.txt"]),
    ("Set-Content -WhatIf a.md x", "powershell", VAULT, []),
    ("git log | Out-File -Verbose a.txt", "powershell", VAULT, ["d:/aurelysn/a.txt"]),
    ("Get-Process | Export-Csv a.csv -NoTypeInformation", "powershell", VAULT, ["d:/aurelysn/a.csv"]),
    ("$script:d = 'D:/AureLysn'; Set-Content \"$script:d/a.md\" x", "powershell", "C:/x", ["d:/aurelysn/a.md"]),
    ("$out = @('x' | Set-Content a.md -PassThru)", "powershell", VAULT, ["d:/aurelysn/a.md"]),
    ("# so sánh a.md -> b.md\nGet-Content a.md", "powershell", VAULT, []),
    ("$h -gt 3; 'a -> b.md'; $x -replace '>', 'y'", "powershell", VAULT, []),
    ("@'\nit's\n'@ | Set-Content a.md", "powershell", VAULT, ["d:/aurelysn/a.md"]),
    ("diff <(git show HEAD:a) > >(tee log.md)", "bash", VAULT, ["d:/aurelysn/log.md"]),
    ("[[ a > b.md ]] && echo x >| c.md", "bash", VAULT, ["d:/aurelysn/c.md"]),
    ("cmd 3>&1 1>&2 > /dev/null 2> err.txt", "bash", VAULT, ["d:/aurelysn/err.txt"]),
    ("cd /c/t && bash -c 'cd sub; echo x > a.md'; echo y > b.md", "bash", VAULT, ["c:/t/sub/a.md", "c:/t/b.md"]),
    ("powershell -Command \"Set-Content a.md 'x'\"", "bash", VAULT, ["d:/aurelysn/a.md"]),
    ("Start-Process cmd -ArgumentList '/c echo x > a.md' -WorkingDirectory C:/t", "powershell", VAULT, ["c:/t/a.md"]),
]

# (command, shell, [(shell, program)] that must appear among the simple commands)
KINDS = [
    ("cmd /c \"python x.py > a.md\"; 'y' > b.md", "powershell", [("cmd", "python"), ("powershell", "y")]),
    ("bash -c 'git status'", "powershell", [("bash", "git")]),
    ("powershell -NoProfile -Command \"Get-Date\"", "bash", [("powershell", "get-date")]),
    ("echo 'git add -A' | bash", "bash", [("bash", "git")]),
    ("'git add -A' | iex", "powershell", [("powershell", "git")]),
    ("for i in 1 2; do python x.py; done", "bash", [("bash", "python")]),
    ("$r = Get-Date", "powershell", [("powershell", "get-date")]),
    ("[string]$o = python x.py; $o += git log; $script:p = gh pr list", "powershell",
     [("powershell", "python"), ("powershell", "git"), ("powershell", "gh")]),
]


def walk_written(cmd: str, cwd: str, text_only: bool = False, shell: str | None = None) -> set[str]:
    return {path for c in walk(cmd, cwd, shell) for _, path in written_files(c, text_only)}


def main() -> int:
    checks: list[tuple[str, object, object]] = []
    for cmds, start, want in CD:
        scope = Scope(start)
        for c in cmds:
            scope.step(c)
        checks.append((" ; ".join(cmds), scope.cwd, want))
    for seg, want in REDIRECTS:
        checks.append((seg, redirect_targets(seg), want))
    for cmd, cwd, want in WRITTEN:
        checks.append((cmd, walk_written(cmd, cwd), set(want)))
    for cmd, cwd, want in TEXT:
        checks.append((f"{cmd} (chữ)", walk_written(cmd, cwd, True), set(want)))
    for cmd, shell, cwd, want in SHELL_TEXT:
        checks.append((f"{shell}: {cmd}", walk_written(cmd, cwd, True, shell), set(want)))
    for cmd, shell, want in KINDS:
        kinds = {(c.shell, c.program) for c in walk(cmd, VAULT, shell)}
        checks.append((f"{shell}: {cmd} (shell)", set(want) <= kinds, True))
    checks.append(("đường dẫn của công cụ file không có biến", Scope(VAULT).literal("06_Station/$id 100%x%.md"),
                   "d:/aurelysn/06_station/$id 100%x%.md"))
    # variables and cwd reach the body of an `if`, from the segment that holds it
    seen = [(c.cwd, c.scope.expand("$sp"), c.text.strip()) for c in
            walk("$sp = 'C:/t/scratchpad/x'; if (Test-Path $sp) { Remove-Item -Recurse $sp }", VAULT, "powershell")]
    checks.append(("biến gán trước khối if", ("d:/aurelysn", "C:/t/scratchpad/x", "Remove-Item -Recurse $sp") in seen, True))
    seen2 = [(c.cwd, c.text.strip()) for c in walk("cd /d/AureLysn; if true; then (rm a.md); fi; cd /c/x", "C:/y", "bash")]
    checks.append(("cd sau khối không áp vào khối", ("d:/aurelysn", "rm a.md") in seen2 and ("c:/x", "rm a.md") not in seen2, True))

    failed = 0
    for label, got, want in checks:
        ok = got == want
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] {label!r}" + ("" if ok else f"  được {got!r}, muốn {want!r}"))
    print(f"\n{len(checks) - failed}/{len(checks)} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
