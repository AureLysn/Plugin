#!/usr/bin/env python3
"""PreToolUse rule engine: run the hook rules that live in the vault as notes (`chạy luật` = run
rules; vault-ops 0.10.0, plugin-benchmark-20261124 V2).

A lesson recorded by `ghi-loi` becomes a note in `01_Origine/05_Meta/Rules/hook/` with one
```toml block (format, fields and lifecycle: `hook-rule-format` in that folder). Notes are
read at run time, so a new rule needs no version bump or plugin sync. They are always read from
the vault's MAIN tree, also when the session works in a worktree: only merged rules bind.

  status: draft (also review, wip)  shadow: a match is logged, nothing is said or blocked
  status: active                    enforced: warn (text for Claude), ask (permission prompt), block
  superseded, archived, rejected    off: not run, not checked

Shell rules see every simple command (`duong_dan.walk`: wrapped commands, `cd` and variables
followed), file rules see Write / Edit / MultiEdit / NotebookEdit. The strictest matching active
rule decides; draft rules are looked at only when none matched. What cannot run is skipped and
reported by `--check`, `vault_doctor` and `nhac_ban_giao.py` (session start): a rule that cannot be
read, and an ask or block rule that hits an everyday call (`everyday_calls`, plus a neutral command in
the current context), so most rules that are too broad cannot lock a session out. Unreadable
payloads follow `GIT_GUARD_STRICT` (`tach_lenh.unreadable`). A watchdog ends the hook without a
decision when a regex runs away.

Matches are logged to `${CLAUDE_PLUGIN_DATA}/luat-hook.jsonl`: time, rule, status, action, tool
and the first eight characters of the session id — never the command or file text.

    python chay_luat.py --check [--vault DIR]          validate every rule note, examples included
    python chay_luat.py --try "<command>" [--tool Bash] [--cwd DIR] [--content TEXT] [--vault DIR]
    python chay_luat.py --try -                        the same, the command read from stdin
    python chay_luat.py --stats [--log FILE]           hits per rule

Exit (hook): 0 = allow, warn, or ask on Claude Code; 1 = the hook failed, the call goes on;
2 = block, or ask on another host. Exit (--check): 0 = valid, 2 = a rule is broken or no vault.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import tomllib

    from duong_dan import Scope, is_absolute, protected, walk, written_files
    from tach_lenh import decode, shell_of, unreadable
    HELPERS = ""
except Exception as _e:  # Python < 3.11 or a helper missing: the fail mode decides
    HELPERS = f"thiếu tach_lenh.py, duong_dan.py hoặc tomllib ({type(_e).__name__})"

    def unreadable(reason: str, default: int = 0) -> int:
        if os.environ.get("GIT_GUARD_STRICT", "").strip().lower() not in ("1", "true", "yes", "on"):
            return default
        print(f"CHẶN (GIT_GUARD_STRICT=1): engine luật hook không chạy được ({reason}).", file=sys.stderr)
        return 2

FORMAT = 1
RULES_REL = Path("01_Origine/05_Meta/Rules/hook")
DEFAULT_VAULT = Path("D:/AureLysn")
LOG_NAME = "luat-hook.jsonl"
LOG_MAX = 1_000_000
MAX_TEXT = 20_000      # characters of a value a regex may see
MAX_MESSAGE = 1_200
WATCHDOG = float(os.environ.get("CHAY_LUAT_WATCHDOG", "6"))  # seconds before a run gives up (hooks.json allows 10)

SHELL_TOOLS = ("Bash", "PowerShell", "run_command")
FILE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
TOOLS = {"shell": SHELL_TOOLS, "file": FILE_TOOLS}
FIELDS = {
    "shell": {"program", "args", "segment", "bare", "command", "cwd", "shell", "tool",
              "writes", "writes_in_vault", "changes", "changes_in_vault"},
    "file": {"path", "path_in_vault", "content", "cwd", "tool"},
}
OPERATORS = ("regex", "in", "equals")
ACTIONS = ("warn", "ask", "block")
STRENGTH = {"block": {"hard"}, "ask": {"hard", "target"}, "warn": {"target", "tendency"}}
KEYS = {"format", "event", "action", "where", "tools", "message", "when", "any", "unless", "match", "pass"}
EXAMPLE_KEYS = {"shell": {"tool", "command", "cwd", "input"}, "file": {"tool", "path", "content", "cwd", "input"}}
SHADOW = {"draft", "review", "wip"}
OFF = {"superseded", "archived", "rejected"}

# Everyday calls an ask or block rule may not touch (for a warn rule `--check` only says so). Each
# command is tried with every shell tool of the rule and from each folder.
EVERYDAY_COMMANDS = (
    "git status --short", "git diff --stat", "git log --oneline -3", "git add 06_Station/a.md",
    'git commit -m "docs: cập nhật note"', "ls -la", "cat a.md", "cd 01_Origine", "git status --short\nls",
    "python 01_Origine/04_Tools/VaultTool/Core/vault_doctor.py --include-fiction",
    "git -C D:/AureLysn status --short", "cd /d/AureLysn && ls 06_Station",
    "Get-Content CLAUDE.md -Encoding utf8", "Get-ChildItem 01_Origine",
)
EVERYDAY_FOLDERS = ("D:/AureLysn", "D:/AureLysn/01_Origine", "D:/AureLysn-wt/x", "C:/Users/x")
EVERYDAY_INPUT = {"description": "Show the current state", "timeout": 120000}
EVERYDAY_PATHS = ("D:/AureLysn/06_Station/canary.md", "D:/AureLysn/01_Origine/05_Meta/canary.md",
                  "D:/AureLysn/03_Atelier/canary.md", "D:/AureLysn-wt/x/06_Station/canary.md", "C:/Users/x/canary.md")
EVERYDAY_NOTE = ("---\nid: note.canary\ntype: note\nstatus: draft\naliases: [\"canary\"]\nlast_updated: 2026-11-24\n---\n\n"
                 "# Canary\n\nMột đoạn văn đủ dài để giống một note thật của vault.\n\nĐoạn thứ hai.\n")
# Texts that expose a regex with catastrophic backtracking (`--check` only).
SLOW_TEXTS = ["a" * 4000 + "!", " " * 4000 + "!", "ab " * 1300 + "!", "\\" * 4000 + "!", "-x=" * 1300 + "!",
              "git add " * 500 + "!", "\"" * 4000 + "!", "a/" * 2000 + "!", "0" * 4000 + "!", "a.b-c/" * 600 + "!"]

FRONT = re.compile(r"\A\s*---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.S)
BLOCK = re.compile(r"^```toml[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
QUOTED = re.compile(r'"[^"]*"|\'[^\']*\'')


# --------------------------------------------------------------------- where the vault is

def as_path(p: str) -> Path:
    m = re.match(r"^/([a-zA-Z])(/.*)?$", p)  # Git Bash: /d/AureLysn
    return Path(f"{m.group(1)}:{m.group(2) or '/'}" if m else p)


def vault_above(start: Path) -> Path | None:
    for c in [start, *start.parents]:
        if (c / "CLAUDE.md").is_file() and (c / "01_Origine").is_dir():
            return c
    return None


def main_tree(cwd: str | None) -> Path | None:
    """The vault's main tree: AURELYSN_VAULT, the vault above `cwd` (a worktree leads to the tree
    it was cut from), else the default location."""
    env = os.environ.get("AURELYSN_VAULT")
    if env and vault_above(Path(env)) == Path(env):
        return Path(env)
    found = None
    if cwd:
        try:
            found = vault_above(as_path(cwd))
        except (OSError, ValueError):
            found = None
    if found is not None and not (found / ".git").is_file():
        return found
    if found is not None:  # a worktree: "gitdir: D:/AureLysn/.git/worktrees/<name>", maybe relative
        text = (found / ".git").read_text(encoding="utf-8", errors="replace")
        m = re.match(r"gitdir:\s*(.+?)[\\/]\.git[\\/]worktrees[\\/]", text)
        main = (found / m.group(1)).resolve() if m else None
        if main is not None and vault_above(main) == main:
            return main
    return DEFAULT_VAULT if vault_above(DEFAULT_VAULT) == DEFAULT_VAULT else None


def in_vault(path: str | None) -> str | None:
    """Path relative to the vault or worktree that holds it (lower case, `/`), else None."""
    if not path:
        return None
    m = re.match(r"^d:/aurelysn(?:-wt/[^/]+)?(?:/(.*))?$", path)
    return (m.group(1) or "") if m else None


# --------------------------------------------------------------------- what a call looks like

class Call:
    """One simple shell command, or one file edit: the values a rule's fields can read."""

    def __init__(self, event: str, tool: str, ti: dict, cwd: str | None) -> None:
        self.event, self.tool, self.ti = event, tool, ti
        self.data: dict[str, list] = {"tool": [tool], "cwd": [cwd or ""]}
        self.touches_vault = False

    def values(self, field: str) -> list:
        if field.startswith("input."):
            return [self.ti.get(field[6:])]
        return self.data.get(field, [])


def shell_calls(command: str, tool: str, ti: dict, cwd: str | None) -> list[Call]:
    out: list[Call] = []
    shell = shell_of({"tool_name": tool})
    for c in walk(command, cwd, shell):
        writes = [p for _, p in written_files(c, text_only=True)]
        changes = [p for _, p in written_files(c)]
        call = Call("shell", tool, ti, c.cwd)
        call.data.update({
            "program": [c.program], "args": [" ".join(re.sub(r"\s+", " ", t.value) for t in c.args)],
            "segment": [decode(c.text).strip()], "bare": [QUOTED.sub('""', c.text).strip()],
            "command": [command], "shell": [c.shell or ""],
            "writes": writes, "writes_in_vault": [r for r in map(in_vault, writes) if r is not None],
            "changes": changes, "changes_in_vault": [r for r in map(in_vault, changes) if r is not None],
        })
        named = [p for t in c.args if is_absolute(t.value) for p in [c.scope.resolve(t.value)] if p]
        call.touches_vault = c.scope.cwd_protected() or any(protected(p) for p in changes + named)
        out.append(call)
    if not out:  # only `cd` or assignments: whole-command fields can still match
        call = Call("shell", tool, ti, Scope(cwd).cwd)
        call.data.update({"command": [command], "segment": [command], "bare": [QUOTED.sub('""', command)],
                          "shell": [shell or ""]})
        call.touches_vault = Scope(cwd).cwd_protected()
        out.append(call)
    return out


def new_text(ti: dict) -> list[str]:
    texts = [ti.get(k) for k in ("content", "new_string", "new_source")]
    edits = ti.get("edits")
    for e in edits if isinstance(edits, list) else []:
        if isinstance(e, dict):
            texts.append(e.get("new_string"))
    return [t for t in texts if isinstance(t, str)]


def file_calls(raw_path: str, tool: str, ti: dict, cwd: str | None) -> list[Call]:
    scope = Scope(cwd)
    path = scope.literal(raw_path)
    call = Call("file", tool, ti, scope.cwd)
    rel = in_vault(path)
    call.data.update({"path": [path] if path else [], "path_in_vault": [rel] if rel is not None else [],
                      "content": new_text(ti)})
    call.touches_vault = path is not None and protected(path)
    return [call]


def calls_of(tool: str, ti: dict, cwd: str | None) -> list[Call]:
    if tool in FILE_TOOLS:
        raw = ti.get("file_path") or ti.get("notebook_path") or ""
        return file_calls(raw, tool, ti, cwd) if isinstance(raw, str) else []
    cmd = ti.get("command") or ti.get("CommandLine") or ""
    return shell_calls(cmd, tool, ti, cwd) if isinstance(cmd, str) and cmd.strip() else []


# --------------------------------------------------------------------- rules

class Cond:
    def __init__(self, field: str, op: str, value) -> None:
        self.field, self.op, self.value = field, op, value
        self.rx = re.compile(value, re.I) if op == "regex" else None
        self.items = {str(v).casefold() for v in value} if op == "in" else set()
        self.seen: dict[str, bool] = {}  # whole-command fields come back for every simple command

    def found(self, text: str) -> bool:
        if text not in self.seen:
            self.seen[text] = self.rx.search(text[:MAX_TEXT]) is not None
        return self.seen[text]

    def holds(self, call: Call) -> bool:
        vals = [v for v in call.values(self.field) if v is not None]
        if self.op == "regex":
            return any(self.found(str(v)) for v in vals)
        if self.op == "in":
            return any(str(v).casefold() in self.items for v in vals)
        if isinstance(self.value, str):
            return any(isinstance(v, str) and v.casefold() == self.value.casefold() for v in vals)
        return any(type(v) is type(self.value) and v == self.value for v in vals)


class Rule:
    def __init__(self, name: str) -> None:
        self.name = name
        self.status = self.strength = self.authority = ""
        self.event = self.action = self.message = ""
        self.where = "vault"
        self.tools: tuple[str, ...] = ()
        self.when: list[Cond] = []
        self.any: list[Cond] = []
        self.unless: list[Cond] = []
        self.examples: list[tuple[bool, dict]] = []  # (must match, example)
        self.problems: list[str] = []

    @property
    def off(self) -> bool:
        return self.status in OFF

    def hits(self, call: Call) -> bool:
        if call.event != self.event or call.tool not in self.tools:
            return False
        if self.where == "vault" and not call.touches_vault:
            return False
        if not all(c.holds(call) for c in self.when) or any(c.holds(call) for c in self.unless):
            return False
        return not self.any or any(c.holds(call) for c in self.any)

    def hits_any(self, calls: list[Call]) -> bool:
        return any(self.hits(c) for c in calls)

    def everyday_hit(self) -> str | None:
        """The first everyday call this rule matches, or None."""
        for tool, ti, cwd in everyday_calls(self.event, self.tools):
            if self.hits_any(calls_of(tool, ti, cwd)):
                return f"{tool} {ti.get('command') or ti.get('file_path') or ti.get('notebook_path')!s} ({cwd})"
        return None

    def context_only(self, tool: str, ti: dict, cwd: str | None) -> bool:
        """Does the rule match a neutral command in this very context (tool, folder, other input)?"""
        if self.event != "shell":
            return False
        key = "CommandLine" if "CommandLine" in ti and "command" not in ti else "command"
        return any(self.hits_any(calls_of(tool, {**ti, key: c}, cwd)) for c in ("git status --short", "git status --short\nls"))


def everyday_calls(event: str, tools: tuple[str, ...]):
    if event == "shell":
        for tool in tools:
            for cwd in EVERYDAY_FOLDERS:
                for command in EVERYDAY_COMMANDS:
                    yield tool, {**EVERYDAY_INPUT, "command": command}, cwd
        return
    for tool in tools:
        for path in EVERYDAY_PATHS:
            ti: dict = {("notebook_path" if tool == "NotebookEdit" else "file_path"): path}
            if tool == "Write":
                ti["content"] = EVERYDAY_NOTE
            elif tool == "NotebookEdit":
                ti["new_source"] = EVERYDAY_NOTE
            elif tool == "MultiEdit":
                ti["edits"] = [{"old_string": "Đoạn cũ của note.", "new_string": EVERYDAY_NOTE}]
            else:
                ti.update(old_string="Đoạn cũ của note.", new_string=EVERYDAY_NOTE, replace_all=False)
            yield tool, ti, "D:/AureLysn"


def example_calls(event: str, ex: dict) -> list[Call]:
    """The calls an example stands for; its default working directory is the vault."""
    cwd = ex.get("cwd", "D:/AureLysn")
    ti = dict(ex.get("input") or {})
    if event == "file":
        ti.setdefault("notebook_path" if ex["tool"] == "NotebookEdit" else "file_path", ex.get("path", ""))
        key = {"Edit": "new_string", "MultiEdit": "new_string", "NotebookEdit": "new_source"}.get(ex["tool"], "content")
        ti.setdefault(key, ex.get("content", ""))
    else:
        ti.setdefault("command", ex.get("command", ""))
    return calls_of(ex["tool"], ti, cwd)


def conditions(rule: Rule, key: str, raw, required: bool) -> list[Cond]:
    out: list[Cond] = []
    if not isinstance(raw, list) or not all(isinstance(c, dict) for c in raw):
        rule.problems.append(f"`{key}` phải là các bảng [[{key}]]")
        return out
    if required and not raw:
        rule.problems.append(f"cần ít nhất một [[{key}]]")
    for c in raw:
        field = c.get("field")
        ops = [o for o in OPERATORS if o in c]
        known = isinstance(field, str) and (field in FIELDS.get(rule.event, set())
                                            or re.fullmatch(r"input\.\w+", field))
        if not known:
            rule.problems.append(f"[[{key}]]: trường lạ `{field}` với event `{rule.event}`")
            continue
        if len(ops) != 1 or set(c) - {"field", *OPERATORS}:
            rule.problems.append(f"[[{key}]] `{field}`: cần đúng một trong {', '.join(OPERATORS)}, không có khoá khác")
            continue
        op, value = ops[0], c[ops[0]]
        if op == "regex" and not isinstance(value, str) or op == "in" and not isinstance(value, list):
            rule.problems.append(f"[[{key}]] `{field}`: giá trị của `{op}` sai kiểu")
            continue
        try:
            out.append(Cond(field, op, value))
        except Exception as e:  # re.error, OverflowError, RecursionError
            rule.problems.append(f"[[{key}]] `{field}`: regex hỏng ({e})")
    if key == "when" and out and all(c.rx is not None and c.rx.search("") for c in out):
        rule.problems.append("mọi [[when]] đều khớp cả chuỗi rỗng: luật không thu hẹp gì")
    return out


def examples(rule: Rule, key: str, raw, must_match: bool) -> None:
    if not isinstance(raw, list) or not all(isinstance(e, dict) for e in raw) or not raw:
        rule.problems.append(f"cần ít nhất một [[{key}]]")
        return
    main_key = "command" if rule.event == "shell" else "path"
    for e in raw:
        if set(e) - EXAMPLE_KEYS.get(rule.event, set()) or e.get("tool") not in TOOLS.get(rule.event, ()):
            rule.problems.append(f"[[{key}]]: khoá hoặc tool sai trong {e!r}"[:200])
        elif not isinstance(e.get(main_key), str) or not isinstance(e.get("input", {}), dict) \
                or not isinstance(e.get("cwd", ""), str) or not isinstance(e.get("content", ""), str):
            rule.problems.append(f"[[{key}]]: thiếu `{main_key}`, hoặc `cwd`, `content`, `input` sai kiểu")
        else:
            rule.examples.append((must_match, e))


def front_value(raw: str) -> str:
    """A front-matter value as vaultlib reads it: quotes and a ` # comment` dropped."""
    raw = raw.strip()
    if raw[:1] in ("'", '"') and raw.find(raw[0], 1) > 0:
        return raw[1:raw.find(raw[0], 1)].strip()
    return re.sub(r"\s+#.*$", "", raw).strip()


def read_rule(path: Path) -> Rule | None:
    """The rule a note holds (with its problems), or None when the note is not a rule."""
    rule = Rule(path.stem)
    try:
        return _read_rule(path, rule)
    except Exception as e:  # nothing in one note may stop the others
        rule.problems.append(f"không đọc được ({type(e).__name__}: {e})"[:200])
        return rule


def _read_rule(path: Path, rule: Rule) -> Rule | None:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    m = FRONT.match(text)
    front = {k: front_value(v) for k, v in re.findall(r"^([a-z_]+):[ \t]*(.*)$", m.group(1), re.M)} if m else {}
    blocks = BLOCK.findall(text[m.end():] if m else text)
    rule.status, rule.strength, rule.authority = (front.get(k, "") for k in ("status", "strength", "authority"))
    if front.get("type") != "rule":
        if not blocks:
            return None
        rule.problems.append(f"có khối ```toml nhưng type là `{front.get('type', '')}`, không phải rule")
        return rule
    if rule.off:
        return rule
    if rule.status != "active" and rule.status not in SHADOW:
        rule.problems.append(f"status lạ `{rule.status}`: cần active, {', '.join(sorted(SHADOW | OFF))}")
    if len(blocks) != 1:
        rule.problems.append(f"cần đúng một khối ```toml, đang có {len(blocks)}")
        return rule
    try:
        d = tomllib.loads(blocks[0])
    except tomllib.TOMLDecodeError as e:
        rule.problems.append(f"TOML hỏng: {e}")
        return rule
    unknown = set(d) - KEYS
    if unknown:
        rule.problems.append(f"khoá lạ: {', '.join(sorted(unknown))}")
    if d.get("format") != FORMAT:
        rule.problems.append(f"format phải là {FORMAT}, đang là {d.get('format')!r} (engine cũ hơn luật?)"[:160])
    rule.event, rule.action = str(d.get("event", "")), str(d.get("action", ""))
    message = d.get("message")
    rule.where, rule.message = str(d.get("where", "vault")), message.strip() if isinstance(message, str) else ""
    if rule.event not in TOOLS:
        rule.problems.append(f"event phải là {' | '.join(TOOLS)}")
        return rule
    if rule.action not in ACTIONS:
        rule.problems.append(f"action phải là {' | '.join(ACTIONS)}")
    elif rule.strength not in STRENGTH[rule.action]:
        rule.problems.append(f"action `{rule.action}` cần strength {' | '.join(sorted(STRENGTH[rule.action]))}, "
                             f"đang là `{rule.strength}`")
    if rule.where not in ("vault", "machine"):
        rule.problems.append("where phải là vault | machine")
    if not 0 < len(rule.message) <= MAX_MESSAGE:
        rule.problems.append(f"message phải là chữ, có 1 đến {MAX_MESSAGE} ký tự")
    if rule.status == "active" and rule.authority != "user":
        rule.problems.append("status active cần authority: user (Aurel đã duyệt)")
    tools = d.get("tools", list(TOOLS[rule.event]))
    if not isinstance(tools, list) or not tools or not all(isinstance(t, str) and t in TOOLS[rule.event] for t in tools):
        rule.problems.append(f"tools phải nằm trong {', '.join(TOOLS[rule.event])}")
    else:
        rule.tools = tuple(tools)
    rule.when = conditions(rule, "when", d.get("when", []), required=True)
    rule.any = conditions(rule, "any", d.get("any", []), required=False)
    rule.unless = conditions(rule, "unless", d.get("unless", []), required=False)
    examples(rule, "match", d.get("match", []), True)
    examples(rule, "pass", d.get("pass", []), False)
    return rule


def load(vault: Path) -> list[Rule]:
    folder = vault / RULES_REL
    if not folder.is_dir():
        return []
    rules = (read_rule(p) for p in sorted(folder.glob("*.md"), key=lambda p: p.name.lower()))
    return [r for r in rules if r is not None]


def check_rule(rule: Rule, skip_examples: bool = False) -> list[str]:
    """Why this rule cannot run as written: structure, examples, everyday calls hit."""
    problems = list(rule.problems)
    if problems or rule.off:
        return problems
    try:
        for must, ex in [] if skip_examples else rule.examples:
            if rule.hits_any(example_calls(rule.event, ex)) != must:
                shown = (ex.get("command") or ex.get("path") or "")[:120]
                problems.append(f"ví dụ {'[[match]] không khớp' if must else '[[pass]] lại khớp'}: {shown}"
                                + (f" ({missing(rule, ex)})" if must else ""))
        broad = rule.everyday_hit() if rule.action != "warn" else None
        if broad:
            problems.append(f"quá rộng: khớp cả lệnh thường ngày: {broad}")
    except Exception as e:
        problems.append(f"lỗi khi thử ({type(e).__name__}: {e})"[:200])
    return problems


def missing(rule: Rule, ex: dict) -> str:
    """For a [[match]] that does not match: what did not hold on the closest call."""
    calls = example_calls(rule.event, ex)
    if ex["tool"] not in rule.tools:
        return f"tool {ex['tool']} không nằm trong tools"
    if rule.where == "vault" and not any(c.touches_vault for c in calls):
        return "lệnh không chạm vault: where = \"vault\""
    best = max(calls, key=lambda c: sum(k.holds(c) for k in rule.when), default=None)
    fails = [k for k in rule.when if best is None or not k.holds(best)]
    if fails:
        k = fails[0]
        return f"[[when]] `{k.field}` {k.op} không giữ; giá trị: {[str(v)[:80] for v in best.values(k.field)]!r}" if best else "không có lệnh nào"
    return "một [[unless]] giữ, hoặc không [[any]] nào giữ"


# --------------------------------------------------------------------- checks with a time limit

def check_child(vault: Path) -> int:
    """Child of `--check` and `check_folder`: one JSON line before and after each rule, so that the
    parent knows which rule was running when the time ran out."""
    skip = set(sys.stdin.read().split("\n")) if not sys.stdin.isatty() else set()
    for r in load(vault):
        if r.name in skip:
            continue
        print(json.dumps({"start": r.name}), flush=True)
        problems = check_rule(r)
        notes = []
        if not problems and not r.off:
            if r.action == "warn":
                broad = r.everyday_hit()
                notes += [f"khớp cả lệnh thường ngày: {broad}"] if broad else []
        if not r.off:
            for c in r.when + r.any + r.unless:
                for t in SLOW_TEXTS if c.rx else []:
                    began = time.perf_counter()
                    c.rx.search(t)
                    if time.perf_counter() - began > 1:
                        problems.append(f"regex của `{c.field}` chạy quá lâu trên chuỗi dài")
                        break
        print(json.dumps({"rule": r.name, "problems": problems, "notes": notes, "status": r.status, "event": r.event,
                          "action": r.action, "match": sum(m for m, _ in r.examples),
                          "pass": sum(not m for m, _ in r.examples), "off": r.off}), flush=True)
    return 0


def run_checks(vault: Path, limit: float | None = None, rounds: int = 6) -> list[dict]:
    """Result of every rule; a rule that runs out of time is reported and the rest still checked,
    for as many rounds as given."""
    import subprocess

    limit = limit or float(os.environ.get("CHAY_LUAT_LIMIT", "15"))  # seconds; tests shorten it
    results: list[dict] = []
    done: list[str] = []
    for _ in range(rounds):
        out, timed_out = b"", False
        try:
            r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--check-child", "--vault", str(vault)],
                               input="\n".join(done).encode("utf-8"), capture_output=True, timeout=limit,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            out = r.stdout
        except subprocess.TimeoutExpired as e:
            out, timed_out = e.stdout or b"", True
        started = None
        for line in out.decode("utf-8", "replace").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if "start" in d:
                started = d["start"]
            else:
                results.append(d)
                done.append(d["rule"])
                started = None
        if not timed_out:
            if started:  # the child died on this rule
                results.append({"rule": started, "problems": ["kiểm tra bị dừng giữa chừng"], "notes": []})
                done.append(started)
                continue
            break
        results.append({"rule": started or "?", "problems": [f"regex chạy quá lâu (quá {limit:g} giây)"], "notes": []})
        if not started:
            break
        done.append(started)
    return results


def broken(vault: Path) -> list[str]:
    """Names of the rules `--check` would report; for nhac_ban_giao.py (its hook has 15 seconds)."""
    return [d["rule"] for d in run_checks(vault, limit=4, rounds=2) if d["problems"]]


def check_folder(vault: Path) -> list[tuple[str, str]]:
    """(note path relative to the vault, problem) for every broken rule; for vault_doctor."""
    return [((RULES_REL / f"{d['rule']}.md").as_posix(), p) for d in run_checks(vault) for p in d["problems"]]


# --------------------------------------------------------------------- hook

def append_locked(path: Path, blob: bytes) -> None:
    """Append under a lock file: hooks of one session run in parallel, and Windows appends are
    not atomic. Gives up after half a second, so a stuck lock costs one log entry, not the hook."""
    lock = path.with_suffix(".lock")
    deadline = time.monotonic() + 0.5
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except OSError:
            try:
                if time.time() - lock.stat().st_mtime > 5:
                    lock.unlink()  # left by a hook that was killed
            except OSError:
                pass
            if time.monotonic() > deadline:
                return
            time.sleep(0.01)
    try:
        if path.exists() and path.stat().st_size > LOG_MAX:
            path.replace(path.with_suffix(".jsonl.1"))
        with open(path, "ab") as f:
            f.write(blob)
    finally:
        os.close(fd)
        try:
            lock.unlink()
        except OSError:
            pass


def log_hits(rules: list[Rule], data: dict, tool: str) -> None:
    folder = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not folder or not rules:
        return
    try:
        path = Path(folder) / LOG_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        session = str(data.get("session_id") or "")[:8]
        lines = [json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "rule": r.name, "status": r.status,
                             "action": r.action, "tool": tool, "session": session}) for r in rules]
        append_locked(path, ("\n".join(lines) + "\n").encode("utf-8", "replace"))
    except Exception:  # the log never changes a decision
        pass


def respond(data: dict, hits: list[Rule]) -> int:
    by = {a: [r for r in hits if r.action == a] for a in ACTIONS}
    text = {a: "\n".join(f"[luật {r.name}] {r.message}" for r in rs) for a, rs in by.items()}
    if by["block"]:
        rest = "\n".join(t for t in (text["ask"], text["warn"]) if t)
        print("CHẶN: " + text["block"] + (f"\n{rest}" if rest else ""), file=sys.stderr)
        return 2
    event = data.get("hook_event_name")
    if event is None:  # another host reads exit codes only
        if by["ask"]:
            print("CHẶN: " + text["ask"], file=sys.stderr)
            return 2
        print(text["warn"], file=sys.stderr)
        return 0
    out: dict = {"hookEventName": event}
    if by["ask"]:
        out["permissionDecision"] = "ask"
        out["permissionDecisionReason"] = text["ask"]
    if by["warn"]:
        out["additionalContext"] = text["warn"]
    print(json.dumps({"hookSpecificOutput": out}, ensure_ascii=False))
    return 0


def matching(rules: list[Rule], calls: list[Call], tool: str, ti: dict, cwd: str | None) -> list[Rule]:
    found = [r for r in rules if r.hits_any(calls)]
    return [r for r in found if r.action == "warn" or not (r.context_only(tool, ti, cwd) or r.everyday_hit())]


def hook() -> int:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace"))
    except Exception:
        return unreadable("stdin không phải JSON")
    ti = (data.get("tool_input") or data.get("toolInput")) if isinstance(data, dict) else None
    if not isinstance(ti, dict):
        return unreadable("không có tool_input")
    if HELPERS:
        return unreadable(HELPERS)
    cwd = data.get("cwd") or data.get("currentWorkingDirectory")
    cwd = cwd if isinstance(cwd, str) and cwd.strip() else os.getcwd()
    tool = str(data.get("tool_name") or data.get("toolName") or "")
    try:
        import faulthandler

        faulthandler.dump_traceback_later(WATCHDOG, exit=True, file=open(os.devnull, "w"))
    except Exception:
        pass
    try:
        vault = main_tree(cwd)
        rules = [r for r in load(vault) if not r.problems and not r.off] if vault else []
        if not rules:
            return 0
        calls = calls_of(tool, ti, cwd)
        hits = matching([r for r in rules if r.status == "active"], calls, tool, ti, cwd)
        if hits:
            log_hits(hits, data, tool)
            return respond(data, hits)
        log_hits(matching([r for r in rules if r.status in SHADOW], calls, tool, ti, cwd), data, tool)
        return 0
    except Exception as e:
        return unreadable(f"engine luật lỗi khi kiểm: {type(e).__name__}: {e}", default=1)


# --------------------------------------------------------------------- command line

def cmd_check(vault: Path) -> int:
    if not (vault / RULES_REL).is_dir():
        print(f"Không có thư mục luật {vault / RULES_REL}", file=sys.stderr)
        return 2
    began = time.time()
    bad = 0
    for d in run_checks(vault):
        bad += bool(d["problems"])
        label = "TẮT " if d.get("off") else ("FAIL" if d["problems"] else "OK  ")
        detail = f" ({d['status']}, {d['event']}, {d['action']}, {d['match']} match + {d['pass']} pass)" if d.get("event") else ""
        print(f"  [{label}] {d['rule']}{detail}")
        for p in d["problems"]:
            print(f"         - {p}")
        for p in d["notes"]:
            print(f"         · {p}")
    print(f"\n{bad} luật hỏng, kiểm trong {time.time() - began:.1f} giây.")
    return 2 if bad else 0


def cmd_try(vault: Path, command: str, tool: str, cwd: str, content: str) -> int:
    if command == "-":
        command = sys.stdin.buffer.read().decode("utf-8-sig", "replace").rstrip("\r\n")
    if tool in FILE_TOOLS:
        key = {"Edit": "new_string", "MultiEdit": "new_string", "NotebookEdit": "new_source"}.get(tool, "content")
        ti = {"file_path": command, key: content}
    else:
        ti = {"command": command}
    calls = calls_of(tool, ti, cwd)
    hits = [r for r in load(vault) if not r.problems and not r.off and r.hits_any(calls)]
    for r in hits:
        print(f"{r.name} ({r.status}, {r.action}): {r.message.splitlines()[0]}")
    if not hits:
        print("Không luật nào khớp.")
    return 0


def cmd_stats(log: Path | None) -> int:
    from collections import Counter

    logs = [log] if log else sorted(Path.home().glob(f".claude/plugins/data/vault-ops*/{LOG_NAME}*"))
    hits, sessions, last = Counter(), {}, {}
    for path in logs:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = json.loads(line)
                key = (d["rule"], d["status"], d["action"])
            except Exception:
                continue
            hits[key] += 1
            sessions.setdefault(key, set()).add(d.get("session"))
            last[key] = max(last.get(key, ""), d.get("t", ""))
    if not hits:
        print("Chưa có lần trúng nào được ghi.")
    for key, n in hits.most_common():
        print(f"{n:>5} lần · {len(sessions[key])} phiên · gần nhất {last[key]} · {key[0]} ({key[1]}, {key[2]})")
    return 0


def main() -> int:
    if len(sys.argv) == 1:
        return hook()
    import argparse

    ap = argparse.ArgumentParser(description="Hook rules of the vault (hook-rule-format).")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--try", dest="command", help="command to try, or - to read it from stdin")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--check-child", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--vault", type=Path, help="vault or worktree to read (default: the one above here)")
    ap.add_argument("--tool", default="Bash", choices=SHELL_TOOLS + FILE_TOOLS)
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--content", default="", help="new text of a file edit, with --tool Write, Edit, …")
    ap.add_argument("--log", type=Path)
    args = ap.parse_args()
    if args.stats:
        return cmd_stats(args.log)
    if HELPERS:
        print(HELPERS, file=sys.stderr)
        return 2
    vault = args.vault or vault_above(Path.cwd())
    if vault is None or vault_above(Path(vault).resolve()) != Path(vault).resolve():
        print(f"Không thấy vault{f' ở {vault}' if vault else ''}: chạy trong vault hoặc thêm --vault DIR", file=sys.stderr)
        return 2
    if args.check_child:
        return check_child(vault)
    if args.command is not None:
        return cmd_try(vault, args.command, args.tool, args.cwd, args.content)
    return cmd_check(vault)


if __name__ == "__main__":
    raise SystemExit(main())
