#!/usr/bin/env python3
"""Tests for chay_luat.py: each hook case is one payload against rule notes in a fake vault
(AURELYSN_VAULT points at it; payload paths stay under D:/AureLysn, the only place the engine
calls "the vault"). Payloads are sent as raw UTF-8, as Claude Code does. `--check` is tested against
one broken note per kind of fault. Cases marked "review" come from the four-agent review of
2026-11-24.

Expected hook result: 0 = silent, 1 = the hook failed, 2 = block, "ask" / "warn" = JSON answer.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ENGINE = Path(__file__).with_name("chay_luat.py")
REPO_VAULT = Path(__file__).resolve().parents[5]
VAULT, WT, HOME = "D:\\AureLysn", "D:\\AureLysn-wt\\x", "C:\\Users\\x"
results: list[tuple[str, bool, str]] = []


def case(label: str, ok: bool, detail: object = "") -> None:
    results.append((label, bool(ok), str(detail)))


def note(status="active", strength="hard", authority="user", toml="", blocks=1, ntype="rule") -> str:
    front = (f"---\nid: rule.hook.x\ntype: {ntype}\nscope: global\nlane: shared\nstatus: {status}\n"
             f"strength: {strength}\nauthority: {authority}\nlast_updated: 2026-11-24\n---\n\n# X\n\n")
    return front + ("```toml\n" + toml.strip() + "\n```\n\n") * blocks


BASE = '''
format = 1
event = "shell"
action = "{action}"
message = "đừng chạy foo {action}"
[[when]]
field = "program"
in = ["foo"]
[[match]]
tool = "Bash"
command = "foo a"
[[pass]]
tool = "Bash"
command = "echo foo"
'''
WHEN = '[[when]]\nfield = "program"\nin = ["foo"]\n'


def rule(action="block", extra_top="", when="", tail="") -> str:
    text = BASE.replace("{action}", action)
    if extra_top:
        text = text.replace('event = "shell"\n', 'event = "shell"\n' + extra_top + "\n")
    if when:
        text = text.replace(WHEN, when)
    return text + tail


def cond(field: str, op: str, value: str, key="when") -> str:
    return f'[[{key}]]\nfield = "{field}"\n{op} = {value}\n'


def make_vault(root: Path, rules: dict[str, str]) -> Path:
    (root / "01_Origine/05_Meta/Rules/hook").mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text("# c\n", encoding="utf-8")
    for name, text in rules.items():
        (root / "01_Origine/05_Meta/Rules/hook" / f"{name}.md").write_text(text, encoding="utf-8", newline="")
    return root


def base_env(vault: Path | None, extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("GIT_GUARD_STRICT", "CLAUDE_PLUGIN_DATA", "PYTHONUTF8", "PYTHONIOENCODING", "AURELYSN_VAULT")}
    if vault is not None:
        env["AURELYSN_VAULT"] = str(vault)
    env.update(extra or {})
    return env


def run(vault: Path | None, payload, env_extra: dict | None = None, raw: bytes | None = None,
        engine: Path = ENGINE) -> tuple[object, str, str]:
    data = raw if raw is not None else json.dumps(payload, ensure_ascii=False).encode("utf-8", "surrogatepass")
    try:
        r = subprocess.run([sys.executable, str(engine)], input=data, capture_output=True, env=base_env(vault, env_extra), timeout=40)
    except subprocess.TimeoutExpired:
        return "timeout", "", ""
    out, err = r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
    result: object = r.returncode
    if r.returncode == 0 and out.strip():
        try:
            o = json.loads(out)["hookSpecificOutput"]
            result = o.get("permissionDecision") or ("warn" if o.get("additionalContext") else "json")
        except Exception:
            result = "bad-json"
    return result, out, err


def shell(cmd: str, tool="Bash", cwd=VAULT, claude=True, **inp) -> dict:
    if claude:
        return {"hook_event_name": "PreToolUse", "session_id": "0123456789abcdef", "tool_name": tool, "cwd": cwd,
                "tool_input": {"command": cmd, **inp}}
    return {"toolName": "run_command", "cwd": cwd, "toolInput": {"CommandLine": cmd}}


def file_call(tool: str, path: str, cwd=VAULT, **inp) -> dict:
    return {"hook_event_name": "PreToolUse", "session_id": "0123456789abcdef", "tool_name": tool, "cwd": cwd,
            "tool_input": {("notebook_path" if tool == "NotebookEdit" else "file_path"): path, **inp}}


def cli(vault: Path, *args: str, env_extra: dict | None = None, stdin: str = "") -> tuple[int, str]:
    try:
        r = subprocess.run([sys.executable, str(ENGINE), *args, "--vault", str(vault)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, **(env_extra or {})}, input=stdin, timeout=90)
    except subprocess.TimeoutExpired:
        return -1, "timeout"
    return r.returncode, r.stdout + r.stderr


counter = [0]


def one(tmp: Path, toml: str, **front) -> Path:
    """A fake vault with one rule, called `x`."""
    counter[0] += 1
    return make_vault(tmp / f"one{counter[0]}", {"x": note(toml=toml, **front)})


def decisions(tmp: Path) -> None:
    v = one(tmp, rule("block"))
    got, _, err = run(v, shell("foo a"))
    case("active block -> 2, có tên luật và lời nhắc", got == 2 and "[luật x] đừng chạy foo block" in err, err)
    case("không khớp -> im lặng", run(v, shell("bar a"))[0] == 0)
    case("chỉ nhắc trong echo -> im lặng", run(v, shell("echo foo a"))[0] == 0)
    for label, cmd, tool in (("bash -c", 'bash -c "foo a"', "Bash"), ("khối if", "if ($true) { foo a }", "PowerShell"),
                             ("$( )", "echo $(foo a)", "Bash"), ("heredoc vào bash", "bash <<'EOF'\nfoo a\nEOF", "Bash"),
                             ("do trên một dòng (review)", "for i in 1 2; do foo a; done", "Bash"),
                             ("nối dòng (review)", "echo x; \\\n  foo \\\n  a", "Bash"),
                             ("sau here-string có nháy (review)", "@'\nit's\n'@ | Out-Null; foo a", "PowerShell")):
        case(f"{label} -> 2", run(v, shell(cmd, tool=tool))[0] == 2)
    for label, cmd, tool in (("heredoc của cat", "cat > a.txt <<'EOF'\nfoo a\nEOF", "Bash"),
                             ("chú thích (review)", "git status # rồi; foo a", "Bash"),
                             ("here-string (review)", "git commit -m @'\ndon't; foo a\n'@", "PowerShell")):
        case(f"{label} -> im lặng", run(v, shell(cmd, tool=tool))[0] == 0)
    case("host khác: block -> 2", run(v, shell("foo a", claude=False))[0] == 2)
    case("where vault: ngoài vault -> im lặng", run(v, shell("foo a", cwd=HOME))[0] == 0)
    case("where vault: cd vào vault trước -> 2", run(v, shell("cd /d/AureLysn && foo a", cwd=HOME))[0] == 2)
    case("where vault: trong worktree -> 2", run(v, shell("foo a", cwd=WT))[0] == 2)
    case("where vault: trong kho G: -> 2", run(v, shell("foo a", cwd="G:\\My Drive\\AureLysn\\Storage"))[0] == 2)
    case("where vault: gọi tên file của vault từ ngoài -> 2 (review)", run(v, shell("foo D:/AureLysn/a.py", cwd=HOME))[0] == 2)
    case("where vault: ghi vào vault từ ngoài -> 2", run(v, shell("foo > D:/AureLysn/a.txt", cwd=HOME))[0] == 2)
    case("where vault: cd tới chỗ chưa rõ trong phiên của vault -> 2 (review)",
         run(v, shell('cd "$(git rev-parse --show-toplevel)" && foo a'))[0] == 2)
    case("where vault: cd tới chỗ chưa rõ ngoài vault -> im lặng", run(v, shell('cd "$(pwd)" && foo a', cwd=HOME))[0] == 0)

    v = one(tmp, rule("ask"), strength="target")
    got, out, _ = run(v, shell("foo a"))
    case("active ask -> hỏi, lý do có lời nhắc", got == "ask" and "đừng chạy foo ask" in out, out)
    case("host khác: ask -> 2", run(v, shell("foo a", claude=False))[0] == 2)
    v = one(tmp, rule("warn"), strength="target")
    got, out, _ = run(v, shell("foo a"))
    o = json.loads(out)["hookSpecificOutput"] if out else {}
    case("active warn -> additionalContext, không chặn", got == "warn" and "permissionDecision" not in o
         and o.get("hookEventName") == "PreToolUse" and "đừng chạy foo warn" in o.get("additionalContext", ""), out)
    got, _, err = run(v, shell("foo a", claude=False))
    case("host khác: warn -> 0, nhắc qua stderr", got == 0 and "đừng chạy foo warn" in err)
    both = {"a-block": note(toml=rule("block")), "b-ask": note(strength="target", toml=rule("ask")),
            "c-warn": note(strength="target", toml=rule("warn"))}
    got, _, err = run(make_vault(tmp / "all3", both), shell("foo a"))
    case("block thắng, vẫn kèm lời của ask và warn", got == 2 and "a-block" in err and "b-ask" in err and "c-warn" in err, err)
    got, out, _ = run(make_vault(tmp / "two", {k: t for k, t in both.items() if k != "a-block"}), shell("foo a"))
    case("ask thắng warn, warn thành additionalContext", got == "ask" and "c-warn" in
         json.loads(out)["hookSpecificOutput"].get("additionalContext", ""), out)


def lifecycle_and_log(tmp: Path) -> None:
    data = tmp / "data"
    log = data / "luat-hook.jsonl"
    notes = {s: note(status=s, authority="ai", toml=rule("block")) for s in ("draft", "review", "wip")}
    notes |= {s: note(status=s, toml=rule("block")) for s in ("superseded", "archived", "rejected")}
    got, out, err = run(make_vault(tmp / "status", notes), shell("foo secret-word"), {"CLAUDE_PLUGIN_DATA": str(data)})
    lines = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    case("draft, review, wip: im lặng", got == 0 and not out and not err, err)
    case("draft, review, wip: có log; superseded, archived, rejected: không", sorted(d["rule"] for d in lines) == ["draft", "review", "wip"], lines)
    case("log chỉ có năm trường và 8 ký tự phiên", bool(lines) and set(lines[0]) == {"t", "rule", "status", "action", "tool", "session"}
         and lines[0]["session"] == "01234567", lines)
    case("log không chứa lệnh", "secret-word" not in log.read_text(encoding="utf-8"))
    v = one(tmp, rule("block"))
    run(v, shell("foo a"), {"CLAUDE_PLUGIN_DATA": str(data)})
    case("active cũng được ghi log", '"status": "active"' in log.read_text(encoding="utf-8"))
    v = make_vault(tmp / "mix", {"on": note(toml=rule("block")), "off": note(status="draft", authority="ai", toml=rule("block"))})
    log.unlink()
    run(v, shell("foo a"), {"CLAUDE_PLUGIN_DATA": str(data)})
    case("active đã quyết thì draft không được xét", '"off"' not in log.read_text(encoding="utf-8"))
    v = one(tmp, rule("block").replace('event = "shell"', 'event = "file"').replace(WHEN, cond("content", "regex", "'secret'"))
            .replace('tool = "Bash"\ncommand = "foo a"', 'tool = "Write"\npath = "D:/AureLysn/a.md"\ncontent = "secret"')
            .replace('tool = "Bash"\ncommand = "echo foo"', 'tool = "Write"\npath = "D:/AureLysn/a.md"\ncontent = "x"'))
    got = run(v, file_call("Write", "D:\\AureLysn\\a.md", content="my secret text"), {"CLAUDE_PLUGIN_DATA": str(data)})[0]
    case("log không chứa nội dung file", got == 2 and "secret text" not in log.read_text(encoding="utf-8"))
    log.write_text("x" * 1_000_001, encoding="utf-8")
    run(one(tmp, rule("block")), shell("foo a"), {"CLAUDE_PLUGIN_DATA": str(data)})
    case("log quá 1 MB -> xoay sang .1", (data / "luat-hook.jsonl.1").exists() and log.stat().st_size < 1000)
    log.unlink()
    procs = [subprocess.Popen([sys.executable, str(ENGINE)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              env=base_env(v, {"CLAUDE_PLUGIN_DATA": str(data)})) for _ in range(12)]
    payload = json.dumps(file_call("Write", "D:\\AureLysn\\a.md", content="secret")).encode()
    for p in procs:
        p.stdin.write(payload)
        p.stdin.close()
    codes = {p.wait() for p in procs}
    good = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    case("12 hook song song: đủ 12 dòng log hợp lệ (review)", codes == {2} and len(good) == 12, f"{codes} {len(good)}")
    lock = data / "luat-hook.lock"
    lock.write_text("", encoding="utf-8")
    size = log.stat().st_size
    got = run(v, file_call("Write", "D:\\AureLysn\\a.md", content="secret"), {"CLAUDE_PLUGIN_DATA": str(data)})[0]
    case("log đang bị khoá: bỏ dòng log, vẫn chặn", got == 2 and log.stat().st_size == size and lock.exists())
    os.utime(lock, (time.time() - 60, time.time() - 60))
    run(v, file_call("Write", "D:\\AureLysn\\a.md", content="secret"), {"CLAUDE_PLUGIN_DATA": str(data)})
    case("khoá bỏ quên quá 5 giây: gỡ và ghi tiếp", log.stat().st_size > size and not lock.exists())
    (tmp / "afile").write_text("x", encoding="utf-8")
    case("thư mục dữ liệu là một file: vẫn chặn", run(v, file_call("Write", "D:\\AureLysn\\a.md", content="secret"),
                                                  {"CLAUDE_PLUGIN_DATA": str(tmp / "afile")})[0] == 2)
    case("session_id có surrogate lẻ: vẫn chặn (review)", run(one(tmp, rule("block")), None, {"CLAUDE_PLUGIN_DATA": str(data)},
         raw=b'{"hook_event_name":"PreToolUse","session_id":"\\ud800x","tool_name":"Bash","cwd":"D:/AureLysn","tool_input":{"command":"foo a"}}')[0] == 2)
    code, text = cli(v, "--stats", "--log", str(log))
    case("--stats đếm lần trúng", code == 0 and "lần" in text and "x (active, block)" in text, text)


def fields(tmp: Path) -> None:
    def check(label: str, when: str, hit: list, miss: list, extra="", tail="") -> None:
        v = one(tmp, rule(when=when, extra_top=extra, tail=tail))
        bad = [p for p in hit if run(v, p)[0] != 2] + [p for p in miss if run(v, p)[0] != 0]
        case(label, not bad, [p.get("tool_input") for p in bad])

    S = shell
    check("program: không phân biệt hoa thường, bỏ .exe và đường dẫn", cond("program", "in", '["FOO"]'),
          [S("foo"), S("C:/bin/foo.exe a"), S('"C:/My Dir/Foo.exe" a')], [S("food"), S("echo foo")])
    check("args: bỏ ngoặc, gộp khoảng trắng kể cả xuống dòng (review)", cond("args", "regex", "'^a b c d$'"),
          [S("x 'a b'   c d"), S('x "a\nb" c d')], [S("x a b c")])
    check("segment: lệnh đơn như đã gõ", cond("segment", "regex", "'^foo \"a;b\"$'"), [S('echo x; foo "a;b"')], [S('foo "a"')])
    check("bare: chữ trong ngoặc bị che (review)", cond("bare", "regex", "'--admin'"), [S("foo --admin")], [S('foo "--admin"'), S("foo '--admin'")])
    check("command: cả lệnh, kể cả lệnh chỉ có cd", cond("command", "regex", "'x/y'"), [S("cd x/y"), S("echo 1; ls x/y")], [S("cd x")])
    check("cwd: đi theo cd", cond("cwd", "regex", "'/05_evasion$'") + WHEN,
          [S("cd 05_Evasion && foo"), S("foo", cwd="D:\\AureLysn\\05_Evasion")], [S("foo 05_Evasion")])
    check("shell: vỏ chạy lệnh, không phải công cụ (review)", cond("shell", "equals", '"powershell"') + cond("program", "in", '["foo"]'),
          [S("foo a", tool="PowerShell"), S('powershell -Command "foo a"')], [S("foo a"), S("bash -c 'foo a'", tool="PowerShell")])
    check("tool", cond("tool", "equals", '"powershell"') + cond("program", "in", '["foo"]'), [S("foo", tool="PowerShell")], [S("foo")])
    check("writes: chữ mới, đường dẫn đầy đủ", cond("writes", "regex", "'^c:/t/a\\.json$'"),
          [S("echo x > C:/t/a.json", cwd=VAULT), S("'x' | Set-Content -LiteralPath C:/t/a.json", tool="PowerShell"),
           S("'x' | sc C:/t/a.json", tool="PowerShell"), S("'x' | ac C:/t/a.json", tool="PowerShell")], [S("cp b C:/t/a.json")])
    check("writes_in_vault: trong vault và worktree", cond("writes_in_vault", "regex", "'^01_origine/a\\.json$'"),
          [S("echo x > 01_Origine/a.json"), S("echo x > D:/AureLysn-wt/x/01_Origine/a.json", cwd=HOME)],
          [S("cp a b.json"), S("echo x > C:/t/01_Origine/a.json")])
    check("changes: chép, dời, xoá", cond("changes", "regex", "'^d:/aurelysn/a\\.json$'"),
          [S("cp a.json b"), S("rm a.json"), S("Move-Item a.json b", tool="PowerShell")], [S("cat a.json")])
    check("changes_in_vault", cond("changes_in_vault", "regex", "'\\.json$'"), [S("cp a.json b.json"), S("mkdir x.json")], [S("cat a.json")])
    check("input.*: equals đúng kiểu", WHEN, [S("foo"), S("foo", run_in_background=False), S("foo", run_in_background="true"),
                                            S("foo", run_in_background=1)],
          [S("foo", run_in_background=True)], tail=cond("input.run_in_background", "equals", "true", "unless"))
    check("equals chữ: không phân biệt hoa thường, không phải một phần", cond("args", "equals", '"A B"'), [S("foo a b")], [S("foo a b c")])
    check("in: khớp cả giá trị, không phải một phần", cond("args", "in", '["a", "b"]'), [S("foo A"), S("foo b")], [S("foo ab")])
    check("regex: không phân biệt hoa thường", cond("program", "regex", "'^foo$'"), [S("FOO")], [S("foo2")])
    check("when: mọi điều kiện", WHEN + cond("args", "regex", "'z'"), [S("foo z")], [S("foo a"), S("bar z")])
    check("any: ít nhất một", WHEN, [S("foo wt"), S("foo a", cwd=WT)], [S("foo a")],
          tail=cond("cwd", "regex", "'/aurelysn-wt/'", "any") + cond("args", "regex", "'wt'", "any"))
    check("unless: không điều kiện nào", WHEN, [S("foo a")], [S("foo skip"), S("foo not")],
          tail=cond("args", "regex", "'skip'", "unless") + cond("args", "regex", "'not'", "unless"))
    check("điều kiện phải giữ trên cùng một lệnh đơn", WHEN + cond("args", "regex", "'z'"), [S("foo z; bar a")], [S("foo a; bar z")])
    check("tools giới hạn theo công cụ", WHEN, [S("foo", tool="PowerShell")], [S("foo")], extra='tools = ["PowerShell"]')
    check("where machine: ngoài vault vẫn áp", WHEN, [S("foo", cwd=HOME)], [], extra='where = "machine"')
    check("chỉ 20.000 ký tự đầu của một giá trị", cond("command", "regex", "'TAIL'"), [S("foo " + "a" * 15000 + " TAIL")],
          [S("foo " + "a" * 25000 + " TAIL")])

    ftoml = ('format = 1\nevent = "file"\naction = "block"\nmessage = "không ghi BOM"\n' + cond("path_in_vault", "regex", "'(?:^|/)hooks\\.json$'")
             + cond("content", "regex", "'\\uFEFF'") + '[[match]]\ntool = "Write"\npath = "D:/AureLysn/01_Origine/hooks.json"\ncontent = "\\uFEFF{}"\n'
             '[[pass]]\ntool = "Write"\npath = "D:/AureLysn/01_Origine/hooks.json"\ncontent = "{}"\n')
    v = one(tmp, ftoml)
    p = "D:\\AureLysn\\01_Origine\\hooks.json"
    F = file_call
    for label, payload, want in (
            ("Write có BOM", F("Write", p, content="\ufeff{}"), 2), ("Write không BOM", F("Write", p, content="{}"), 0),
            ("Edit xét new_string", F("Edit", p, old_string="a", new_string="\ufeff"), 2),
            ("Edit không xét old_string", F("Edit", p, old_string="\ufeff", new_string="a"), 0),
            ("MultiEdit xét từng edit", F("MultiEdit", p, edits=[{"new_string": "b"}, {"new_string": "\ufeffd"}]), 2),
            ("MultiEdit edits sai kiểu", F("MultiEdit", p, edits=5), 0),
            ("NotebookEdit xét new_source", F("NotebookEdit", p, new_source="\ufeff"), 2),
            ("ngoài vault", F("Write", "C:\\t\\hooks.json", content="\ufeff{}"), 0),
            ("trong worktree", F("Write", "D:\\AureLysn-wt\\x\\hooks.json", content="\ufeff{}"), 2),
            ("đường dẫn tương đối", F("Write", "hooks.json", content="\ufeff{}"), 2)):
        case(f"file: {label}", run(v, payload)[0] == want)
    v = one(tmp, ftoml.replace(cond("path_in_vault", "regex", "'(?:^|/)hooks\\.json$'"), cond("path", "regex", "'/\\$id 100%x%`a\\.md$'"))
            .replace("01_Origine/hooks.json", "$id 100%x%`a.md"))
    case("file: $, % và ` trong đường dẫn là chữ (review)", run(v, F("Write", "D:\\AureLysn\\$id 100%x%`a.md", content="\ufeff"))[0] == 2)
    v = one(tmp, ftoml.replace(cond("path_in_vault", "regex", "'(?:^|/)hooks\\.json$'"), cond("path", "regex", "'^g:/my drive/aurelysn/'"))
            .replace("D:/AureLysn/01_Origine/hooks.json", "G:/My Drive/AureLysn/a.json"))
    case("file: kho trên G:", run(v, F("Write", "G:\\My Drive\\AureLysn\\a.json", content="\ufeff"))[0] == 2)


def robustness(tmp: Path) -> None:
    v = make_vault(tmp / "vn", {"x": note(toml=rule(when=cond("args", "regex", "'bàn giao|hoàn\\.md'")).replace('"foo a"', '"foo bàn giao"'))})
    case("tiếng Việt: payload UTF-8 thật (review)", run(v, shell('foo "bàn giao"'))[0] == 2 and run(v, shell("foo hoàn.md"))[0] == 2)
    case("payload có BOM ở đầu", run(v, None, raw=b"\xef\xbb\xbf" + json.dumps(shell("foo hoàn.md")).encode())[0] == 2)
    good = note(toml=rule("block"))
    bad = {"toml hỏng": note(toml="format = = 1"), "tools lồng (review)": note(toml=rule(extra_top='tools = [["Bash"]]')),
           "tools là bảng (review)": note(toml=rule(tail='[[tools]]\nname = "Bash"\n')),
           "regex quá lớn (review)": note(toml=rule(when=cond("args", "regex", "'a{99999999999}'"))),
           "số quá dài (review)": note(toml=rule().replace("format = 1", "format = " + "9" * 5000)),
           "TOML lồng sâu (review)": note(toml="a = " + "[" * 3000 + "]" * 3000),
           "ví dụ sai kiểu (review)": note(toml=rule(tail='[[match]]\ntool = "Bash"\ncommand = "foo"\ncwd = 5\n')),
           "message không phải chữ (review)": note(toml=rule().replace('"đừng chạy foo block"', '["a"]'))}
    for label, text in bad.items():
        vb = make_vault(tmp / f"bad-{abs(hash(label))}", {"a-hong": text, "z-tot": good})
        case(f"một note hỏng ({label}) không tắt luật khác", run(vb, shell("foo a"))[0] == 2 and run(vb, shell("ls"))[0] == 0)
    v = make_vault(tmp / "odd", {"khong-phai-luat": "# không có frontmatter\n", "info": note(ntype="info", blocks=0), "x": good})
    case("note khác trong thư mục bị bỏ qua", run(v, shell("foo a"))[0] == 2)
    for label, text in {"CRLF": good.replace("\n", "\r\n"), "BOM": "\ufeff" + good, "chú thích sau status (review)": good.replace(
            "status: active", "status: active  # Aurel 24/11"), "status trong ngoặc": good.replace("status: active", 'status: "active"'),
            "khoảng trắng sau --- (review)": good.replace("---\n", "--- \n"), "NBSP sau status (review)": good.replace(
            "status: active", "status: active\u00a0"), "dòng trống ở đầu (review)": "\n" + good}.items():
        case(f"note {label}: vẫn có hiệu lực", run(make_vault(tmp / f"fm-{abs(hash(label))}", {"x": text}), shell("foo a"))[0] == 2)
    case("active mà authority ai: không có hiệu lực", run(one(tmp, rule("block"), authority="ai"), shell("foo a"))[0] == 0)
    v = one(tmp, rule("block"))
    for label, raw, strict in (("JSON hỏng", b"{hong", 2), ("không có tool_input", b'{"tool_name":"Bash"}', 2),
                               ("tool_input không phải bảng", b'{"tool_input":"x"}', 2)):
        case(f"{label}: cho qua, GIT_GUARD_STRICT chặn", run(v, None, raw=raw)[0] == 0
             and run(v, None, {"GIT_GUARD_STRICT": "1"}, raw=raw)[0] == strict)
    for label, raw in (("cwd là số", b'{"hook_event_name":"P","tool_name":"Bash","cwd":5,"tool_input":{"command":"ls"}}'),
                       ("command là danh sách", b'{"hook_event_name":"P","tool_name":"Bash","tool_input":{"command":["foo"]}}'),
                       ("tool_name rỗng", b'{"hook_event_name":"P","tool_input":{"command":"foo a"},"cwd":"D:/AureLysn"}')):
        case(f"{label}: không lỗi", run(v, None, raw=raw)[0] == 0)
    alone = tmp / "alone"
    alone.mkdir()
    shutil.copy2(ENGINE, alone / ENGINE.name)
    got, _, err = run(v, shell("foo a"), {"GIT_GUARD_STRICT": "1"}, engine=alone / ENGINE.name)
    case("thiếu module: strict chặn và nói lý do (review)", got == 2 and "thiếu" in err, err)
    case("thiếu module: mặc định cho qua", run(v, shell("foo a"), engine=alone / ENGINE.name)[0] == 0)
    broken = tmp / "broken-module"
    broken.mkdir()
    for name in ("chay_luat.py", "tach_lenh.py", "duong_dan.py"):
        shutil.copy2(ENGINE.with_name(name), broken / name)
    with open(broken / "duong_dan.py", "a", encoding="utf-8", newline="\n") as f:
        f.write("\n\ndef walk(*a, **k):\n    raise RuntimeError('x')\n")
    got = run(v, shell("foo a"), engine=broken / "chay_luat.py")[0]
    case("lỗi nội bộ: exit 1, không chặn; strict thì chặn", got == 1
         and run(v, shell("foo a"), {"GIT_GUARD_STRICT": "1"}, engine=broken / "chay_luat.py")[0] == 2, got)
    v = one(tmp, rule(when=cond("command", "regex", "'^(a+)+$'")).replace('"foo a"', '"aa"').replace('"echo foo"', '"b"'))
    got = run(v, shell("a" * 60 + "!"), {"CHAY_LUAT_WATCHDOG": "2"})[0]
    case("regex chạy mãi: dừng, không chặn (review)", got == 1, got)
    v = make_vault(tmp / "slow-draft", {"on": note(toml=rule("block")), "slow": note(status="draft", authority="ai", toml=rule(
        when=cond("command", "regex", "'^(?:[\\w.-]+/?)+\\.zzz$'")).replace('"foo a"', '"a.zzz"').replace('"echo foo"', '"b"'))})
    case("draft chậm không tắt luật active (review)", run(v, shell("foo " + "a/" * 40 + "x"))[0] == 2)
    main = make_vault(tmp / "main", {"x": note(toml=rule("block", extra_top='where = "machine"'))})
    (main / ".git/worktrees/wt").mkdir(parents=True)
    for label, gitdir in (("tuyệt đối", f"{main.as_posix()}/.git/worktrees/wt"), ("tương đối (review)", "../main/.git/worktrees/wt"),
                          ("dấu \\ (review)", f"{main}\\.git\\worktrees\\wt")):
        wt = make_vault(tmp / "wt", {"y": note(toml=rule("block", extra_top='where = "machine"').replace("foo", "wtonly"))})
        (wt / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
        case(f"worktree (gitdir {label}) dùng luật của cây chính", run(None, shell("foo a", cwd=str(wt)))[0] == 2
             and run(None, shell("wtonly a", cwd=str(wt)))[0] == 0)
    case("thư mục con của cây chính cũng tìm ra vault", run(None, shell("foo a", cwd=str(main / "01_Origine")))[0] == 2)
    case("không có thư mục luật -> im lặng", run(make_vault(tmp / "empty", {}), shell("foo a"))[0] == 0)


BROAD = {  # rules that would lock a session out (review): label -> (toml, calls that must stay silent)
    "mọi lệnh": (rule(when=cond("segment", "regex", "'.'")), [shell("foo a"), shell("git diff")]),
    "mọi lệnh có description": (rule(when=cond("input.description", "regex", "'.'")), [shell("foo", description="x")]),
    "mọi lệnh trong worktree": (rule(when=cond("cwd", "regex", "'/aurelysn-wt/'")), [shell("foo", cwd=WT), shell("ls -la", cwd=WT)]),
    "mọi lệnh ngoài vault": (rule(when=cond("cwd", "regex", "'^c:/'"), extra_top='where = "machine"'), [shell("ls", cwd=HOME)]),
    "mọi lệnh run_command": (rule(when=cond("command", "regex", "'.'"), extra_top='tools = ["run_command"]')
                             .replace('tool = "Bash"', 'tool = "run_command"'), [shell("ls", claude=False)]),
    "git trừ status": (rule(when=cond("program", "in", '["git"]'), tail=cond("args", "regex", "'status'", "unless"))
                       .replace('"foo a"', '"git push"'), [shell("git push"), shell("git commit -m x")]),
    "mọi lệnh PowerShell": (rule(when=cond("program", "regex", "'^(?:get-|git|python)'"), extra_top='tools = ["PowerShell"]')
                            .replace('tool = "Bash"\ncommand = "foo a"', 'tool = "PowerShell"\ncommand = "git a"')
                            .replace('tool = "Bash"\ncommand = "echo foo"', 'tool = "PowerShell"\ncommand = "echo foo"'),
                            [shell("git log", tool="PowerShell")]),
    "lệnh nhiều dòng": (rule(when=cond("command", "regex", "'\\n'")).replace('"foo a"', '"foo\\na"'), [shell("ls\npwd")]),
}
BROAD_FILE = ('format = 1\nevent = "file"\naction = "block"\nmessage = "m"\n{tools}' + '{when}'
              '[[match]]\ntool = "{tool}"\npath = "D:/AureLysn/a.md"\ncontent = "x\\ny xx"\n'
              '[[pass]]\ntool = "{tool}"\npath = "C:/t/a.md"\ncontent = "x"\n')


def broad(tmp: Path) -> None:
    for label, (toml, silent) in BROAD.items():
        v = one(tmp, toml)
        code, text = cli(v, "--check")
        case(f"quá rộng ({label}): --check bắt", code == 2 and "quá rộng" in text, text)
        case(f"quá rộng ({label}): không khoá phiên", all(run(v, p)[0] == 0 for p in silent))
    for label, when, tools, tool in (("nội dung nhiều dòng", cond("content", "regex", "'\\n.'"), "", "Write"),
                                     ("đường dẫn bất kỳ", cond("path", "regex", "'.'"), 'tools = ["MultiEdit", "NotebookEdit"]\n', "MultiEdit"),
                                     ("mọi old_string", cond("input.old_string", "regex", "'.'"), 'tools = ["Edit"]\n', "Edit")):
        v = one(tmp, BROAD_FILE.format(when=when, tools=tools, tool=tool))
        code, text = cli(v, "--check")
        case(f"quá rộng, file ({label}): --check bắt", code == 2 and "quá rộng" in text, text)
    v = one(tmp, rule("ask", when=cond("segment", "regex", "'.'")), strength="hard")
    code, text = cli(v, "--check")
    case("luật ask quá rộng cũng bị bỏ qua và bị --check bắt", run(v, shell("git status"))[0] == 0 and code == 2 and "quá rộng" in text, text)
    v = one(tmp, rule("warn", when=cond("program", "regex", "'git|foo'")), strength="target")
    code, text = cli(v, "--check")
    case("luật warn trùng lệnh thường ngày: chỉ ghi chú", code == 0 and "·" in text and run(v, shell("git status"))[0] == "warn", text)
    v = one(tmp, rule(when=cond("cwd", "equals", '"d:/aurelysn/99_rieng"')), strength="hard")
    case("luật chỉ dựa vào thư mục hiện tại: không khoá thư mục đó (review)",
         run(v, shell("foo", cwd="D:\\AureLysn\\99_Rieng"))[0] == 0)
    for label, toml, extra in (
            ("note thiếu frontmatter (review)", 'format = 1\nevent = "file"\naction = "warn"\nmessage = "m"\ntools = ["Write"]\n'
             + cond("path_in_vault", "regex", "'^0[0-9]_.*\\.md$'") + cond("content", "regex", "'\\A---\\n'", "unless")
             + '[[match]]\ntool = "Write"\npath = "D:/AureLysn/01_Origine/a.md"\ncontent = "x"\n'
             '[[pass]]\ntool = "Write"\npath = "D:/AureLysn/01_Origine/a.md"\ncontent = "---\\nid: x\\n"\n', "warn"),
            ("lookahead rỗng nhưng có điều kiện khác (review)", 'format = 1\nevent = "file"\naction = "warn"\nmessage = "m"\ntools = ["Write"]\n'
             + cond("path_in_vault", "regex", "'\\.md$'") + cond("content", "regex", "'\\A(?!---)'")
             + '[[match]]\ntool = "Write"\npath = "D:/AureLysn/a.md"\ncontent = "x"\n'
             '[[pass]]\ntool = "Write"\npath = "D:/AureLysn/a.md"\ncontent = "---\\nid: x\\n"\n', "warn")):
        code, text = cli(one(tmp, toml, strength="target"), "--check")
        case(f"luật hợp lý không bị từ chối: {label}", code == 0, text)


SLOW_RX = "'^foo$|^(?:a+)+$'"
BROKEN = [  # (label, note text, expected words in the report)
    ("hai khối toml", note(toml=rule(), blocks=2), "đúng một khối"),
    ("không có khối toml", note(toml=rule(), blocks=0), "đúng một khối"),
    ("TOML hỏng", note(toml="format = = 1"), "TOML hỏng"),
    ("khoá lạ", note(toml=rule(extra_top='colour = "red"')), "khoá lạ"),
    ("format khác", note(toml=rule().replace("format = 1", "format = 2")), "format phải là 1"),
    ("event lạ", note(toml=rule().replace('"shell"', '"stop"')), "event phải là"),
    ("action lạ", note(toml=rule().replace('action = "block"', 'action = "deny"')), "action phải là"),
    ("strength không hợp block", note(strength="tendency", toml=rule("block")), "cần strength"),
    ("strength không hợp ask", note(strength="tendency", toml=rule("ask")), "cần strength"),
    ("strength không hợp warn", note(strength="hard", toml=rule("warn")), "cần strength"),
    ("where lạ", note(toml=rule(extra_top='where = "home"')), "where phải là"),
    ("message rỗng", note(toml=rule().replace('"đừng chạy foo block"', '""')), "message phải là"),
    ("message là danh sách", note(toml=rule().replace('"đừng chạy foo block"', '["a"]')), "message phải là"),
    ("message quá dài", note(toml=rule().replace('"đừng chạy foo block"', '"' + "a" * 1300 + '"')), "message phải là"),
    ("active mà authority ai", note(authority="ai", toml=rule()), "cần authority: user"),
    ("status lạ", note(status="Active", toml=rule()), "status lạ"),
    ("status rỗng", note(status="", toml=rule()), "status lạ"),
    ("khối toml nhưng type khác", note(ntype="info", toml=rule()), "không phải rule"),
    ("không đóng frontmatter", note(toml=rule()).replace("2026-11-24\n---", "2026-11-24\n"), "không phải rule"),
    ("tools của event khác", note(toml=rule(extra_top='tools = ["Write"]')), "tools phải nằm trong"),
    ("tools lồng danh sách", note(toml=rule(extra_top='tools = [["Bash"]]')), "tools phải nằm trong"),
    ("không có when", note(toml=rule().replace(WHEN, "")), "[[when]]"),
    ("when không phải bảng", note(toml=rule().replace(WHEN, "").replace('event = "shell"', 'event = "shell"\nwhen = "x"')), "các bảng"),
    ("trường lạ", note(toml=rule(when=cond("content", "regex", "'a'"))), "trường lạ"),
    ("khoá lạ trong điều kiện", note(toml=rule(when=WHEN + "note = 1\n")), "đúng một trong"),
    ("hai toán tử", note(toml=rule(when=WHEN + "regex = 'a'\n")), "đúng một trong"),
    ("in không phải danh sách", note(toml=rule(when=cond("program", "in", "'foo'"))), "sai kiểu"),
    ("regex hỏng", note(toml=rule(when=cond("args", "regex", "'('"))), "regex hỏng"),
    ("regex quá lớn", note(toml=rule(when=cond("args", "regex", "'a{99999999999}'"))), "regex hỏng"),
    ("when chỉ khớp chuỗi rỗng", note(toml=rule(when=cond("args", "regex", "'a*'"))), "chuỗi rỗng"),
    ("thiếu match", note(toml=rule().replace('[[match]]\ntool = "Bash"\ncommand = "foo a"\n', "")), "[[match]]"),
    ("thiếu pass", note(toml=rule().split("[[pass]]")[0]), "[[pass]]"),
    ("match không khớp", note(toml=rule().replace('command = "foo a"', 'command = "bar a"')), "không khớp"),
    ("match không khớp: nêu điều kiện", note(toml=rule().replace('command = "foo a"', 'command = "bar a"')), "`program` in không giữ"),
    ("match ngoài vault với where vault", note(toml=rule().replace('command = "foo a"', 'command = "foo a"\ncwd = "C:/x"')), "không chạm vault"),
    ("pass lại khớp", note(toml=rule().replace('command = "echo foo"', 'command = "foo b"')), "lại khớp"),
    ("ví dụ sai tool", note(toml=rule().replace('tool = "Bash"\ncommand = "foo a"', 'tool = "Write"\ncommand = "foo a"')), "tool sai"),
    ("khoá lạ trong ví dụ", note(toml=rule().replace('command = "foo a"', 'command = "foo a"\ncomand = "x"')), "khoá hoặc tool sai"),
    ("ví dụ thiếu command", note(toml=rule().replace('tool = "Bash"\ncommand = "foo a"', 'tool = "Bash"')), "thiếu `command`"),
    ("cwd của ví dụ sai kiểu", note(toml=rule().replace('command = "foo a"', 'command = "foo a"\ncwd = 5')), "sai kiểu"),
    ("regex chậm ở when", note(toml=rule(when=cond("program", "regex", SLOW_RX))), "quá lâu"),
    ("regex chậm ở unless", note(toml=rule(tail=cond("args", "regex", "'^(?:b+)+x$|^(?:a+)+$'", "unless"))), "quá lâu"),
]


def check_cases(tmp: Path) -> None:
    v = make_vault(tmp / "ok", {"foo-block": note(toml=rule("block")), "foo-draft": note(
        status="draft", authority="ai", strength="target", toml=rule("warn")),
        "cu": note(status="superseded", toml="format = 0"), "kho": note(status="archived", blocks=0), "tu-choi": note(status="rejected", blocks=0),
        "doc": note(ntype="info", blocks=0)})
    code, text = cli(v, "--check")
    case("--check: luật đúng -> 0, luật cũ chỉ ghi TẮT (review)", code == 0 and text.count("[OK  ]") == 2 and text.count("[TẮT ]") == 3, text)
    for i, (label, text_note, want) in enumerate(BROKEN):
        v = make_vault(tmp / f"b{i}", {"foo-x": text_note, "tot": note(toml=rule("block"))})
        code, text = cli(v, "--check", env_extra={"CHAY_LUAT_LIMIT": "3"})
        case(f"--check bắt: {label}", code == 2 and want in text and "foo-x" in text, f"exit {code}: {text[:400]}")
        case(f"--check vẫn kiểm luật khác: {label}", "[OK  ] tot" in text, text[:400])
    code, text = cli(tmp / "khong-co", "--check")
    case("--check ở chỗ không phải vault -> 2 (review)", code == 2, text)
    code, text = cli(tmp / "khong-co", "--try", "foo a")
    case("--try ở chỗ không phải vault -> 2 (review)", code == 2, text)
    bare = tmp / "khong-luat"
    (bare / "01_Origine").mkdir(parents=True)
    (bare / "CLAUDE.md").write_text("# c\n", encoding="utf-8")
    code, text = cli(bare, "--check")
    case("--check ở vault chưa có thư mục luật -> 2", code == 2 and "thư mục luật" in text, text)
    v = make_vault(tmp / "try", {"foo-draft": note(status="draft", authority="ai", toml=rule("block")),
                                 "cu": note(status="archived", toml=rule("block"))})
    code, text = cli(v, "--try", "foo a", "--cwd", "D:/AureLysn")
    case("--try nêu luật khớp, kể cả draft, không kể luật tắt", code == 0 and "foo-draft (draft, block)" in text and "cu (" not in text, text)
    code, text = cli(v, "--try", "-", "--cwd", "D:/AureLysn", stdin='foo "a b" \\\\x\n')
    case("--try - đọc lệnh từ stdin (review)", code == 0 and "foo-draft" in text, text)
    code, text = cli(v, "--try", "bar a", "--cwd", "D:/AureLysn")
    case("--try không khớp", code == 0 and "Không luật nào khớp" in text, text)
    code, text = cli(v, "--try", "foo a", "--tool", "bash")
    case("--try với tool gõ sai -> lỗi (review)", code == 2, text)
    f = one(tmp, BROAD_FILE.format(when=cond("content", "regex", "'xx'"), tools="", tool="Write"))
    code, text = cli(f, "--try", "D:/AureLysn/a.md", "--tool", "Write", "--content", "a xx")
    case("--try --content thử luật file (review)", code == 0 and "x (active, block)" in text, text)
    if (REPO_VAULT / "01_Origine/05_Meta/Rules/hook").is_dir():
        code, text = cli(REPO_VAULT, "--check")
        case("các luật thật của vault qua --check", code == 0, text)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test_chay_luat_"))
    try:
        for part in (decisions, lifecycle_and_log, fields, robustness, broad, check_cases):
            folder = tmp / part.__name__
            folder.mkdir()
            part(folder)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = 0
    for label, ok, detail in results:
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] {label}" + (f"\n         {detail.strip()[:500]}" if detail and not ok else ""))
    print(f"\n{len(results) - failed}/{len(results)} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
