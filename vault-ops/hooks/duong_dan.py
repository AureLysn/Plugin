#!/usr/bin/env python3
"""Shared path handling for the hooks that judge file targets (`duong_dan` = path).

Used by `chan_xoa_vinh_vien.py` (plugin-benchmark-20261124 N4), `chan_sua_rao_chan.py` (G6),
the nested-checkout check of `chan_git_pha_huy.py` (V9), all 0.8.0, and by the rule engine of
vault-ops (`chay_luat.py`, V2; a byte-identical copy there): normalise a path as Git Bash,
PowerShell and cmd write it, follow the working directory through `cd` / `pushd` /
`Set-Location`, substitute variables assigned earlier in the same command (and environment
variables), list the files a command writes, and say whether a path is in the vault, a
worktree, a store, the session scratchpad, a temp folder or a cache folder.

`walk(cmd, cwd, shell)` yields every simple command that a command runs, as `Simple`: its program,
words, the shell that runs it and the scope (working directory, variables) it runs in. Wrappers
(`bash -c`, `powershell -Command`, `eval`, …), bodies (`if { }`, `( )`, `$( )`) and heredocs fed to
a shell are entered from the scope of the command that holds them; a `cd` in a body holds for the
rest of that body, not for what follows it.
"""

from __future__ import annotations

import os
import posixpath
import re

from tach_lenh import (ENV_ASSIGN, IEX_NAMES, PS_SHELLS, SH_SHELLS, SUBST, Body, Normalised, Tok, _skip_quoted, decode,
                       flat, groups, next_word, normalise, program_name, skip_prefixes, split_segments, strip_keywords,
                       tokenize, unwrap)

# Where only Aurel may delete for good (CLAUDE.md Invariant 3). Store paths: stores.md.
PROTECTED_ROOTS = ("d:/aurelysn", "d:/aurelysn-wt", "g:/my drive/aurelysn")
CACHE_DIRS = {"__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache"}

MAX_DEPTH = 10        # bodies inside bodies
MAX_COMMANDS = 1_000  # simple commands of one call

# Programs that give a file new text. The PowerShell ones take one target: -Path, -LiteralPath
# or -FilePath, else the first positional word; Bash `tee` takes every operand.
PS_TEXT_WRITERS = {"set-content", "sc", "add-content", "ac", "out-file", "tee-object", "export-csv", "epcsv"}
TEXT_WRITERS = PS_TEXT_WRITERS | {"tee"}
# Programs whose operands are files they write, move, create or delete.
WRITERS = TEXT_WRITERS | {
    "cp", "copy", "copy-item", "cpi", "mv", "move", "move-item", "mi", "ren", "rename",
    "rename-item", "rni", "rm", "del", "erase", "remove-item", "ri", "rd", "rmdir", "unlink",
    "new-item", "ni", "mkdir", "md", "clear-content", "clc", "ln", "install", "touch", "truncate",
}
PS_PATH_PARAMS = ("path", "literalpath", "filepath", "pspath", "lp")
PS_SWITCHES = ("append", "force", "noclobber", "nonewline", "passthru", "whatif", "confirm", "verbose", "debug",
               "notypeinformation", "useculture", "asbytestream", "includetypeinformation", "nti", "wi", "cf")
NOT_FILES = {"&1", "&2", "/dev/null", "$null", "nul", "null", "/dev/stdout", "/dev/stderr"}

_SCOPED = r"(?:env|script|global|local|private|using):"
VAR_RE = re.compile(rf"\$\{{(?:{_SCOPED})?(\w+)\}}|\$(?:{_SCOPED})?(\w+)|%(\w+)%", re.I)
# The cmd switch in `cd /d D:\x` needs a space after it: `cd /d/AureLysn` (Git Bash) is a path.
CD_RE = re.compile(
    r"^\s*(cd|chdir|pushd|set-location|sl|push-location)(?=\s|$)"
    r"(?:\s+(?:-path|-literalpath|/d|--)(?=\s+\S))?\s*(.*)$", re.I | re.S)
POP_RE = re.compile(r"^\s*(?:popd|pop-location)\s*$", re.I)
PS_ASSIGN = re.compile(rf"^\s*(?:\[[\w.\[\], ]+\]\s*)*\$(?:{_SCOPED})?(\w+)\s*(\+?=)(?!=)\s*(.*?)\s*$", re.S | re.I)
CMD_SET = re.compile(r"^\s*set\s+\"?(\w+)=(.*?)\"?\s*$", re.I | re.S)
EXPRESSION = re.compile(r"^(?:\(|\[[\w.]+\]::|@)")  # a PowerShell expression: its value is not known


def drop_assignment(seg: str) -> str:
    """`$r = Remove-Item x` -> `Remove-Item x` (the command a PowerShell assignment runs)."""
    m = PS_ASSIGN.match(seg)
    return m.group(3) if m else seg


def env_value(name: str) -> str | None:
    key = name.lower()
    for k, v in os.environ.items():
        if k.lower() == key:
            return v
    if key == "home":
        return os.path.expanduser("~")
    return None


def norm(p: str) -> str:
    """One form for an absolute path: `D:\\AureLysn\\x`, `/d/AureLysn/x` -> `d:/aurelysn/x`."""
    s = p.strip().replace("\\", "/")
    if s.startswith(("//?/", "//./")):
        s = s[4:]
    m = re.match(r"^/([a-zA-Z])(/.*)?$", s)
    if m:
        s = f"{m.group(1)}:{m.group(2) or '/'}"
    drive = ""
    m = re.match(r"^([a-zA-Z]{1,8}):/?(.*)$", s)  # d:, d:/x, HKCU:\x
    if m:
        drive, s = m.group(1).lower() + ":", "/" + m.group(2)
    s = posixpath.normpath(s.lower()) if s else "/"
    return drive + s


def is_absolute(text: str) -> bool:
    return bool(re.match(r"^(?:/|\\\\|[a-zA-Z]{1,8}:)", text))


def protected(path: str) -> bool:
    return any(path == r or path.startswith(r + "/") for r in PROTECTED_ROOTS)


def holds_protected(path: str) -> bool:
    """True when deleting `path` with everything under it would take a protected root too."""
    base = path.rstrip("/")
    return base in ("", "d:", "g:") or any(r.startswith(base + "/") for r in PROTECTED_ROOTS)


def scratch_or_cache(path: str) -> bool:
    parts = path.split("/")
    if "scratchpad" in parts or any(p in CACHE_DIRS for p in parts):
        return True
    temps = ["/tmp", "/var/tmp"] + [norm(v) for v in map(env_value, ("TEMP", "TMP", "TMPDIR")) if v]
    return any(path == t or path.startswith(t + "/") for t in temps)


class Scope:
    """Working directory and variables while a command runs segment by segment. `cwd` is None
    when a `cd` went somewhere unknown; `origin` is where the command started."""

    def __init__(self, cwd: str | None) -> None:
        self.cwd = self.origin = norm(cwd) if cwd else None
        self.vars: dict[str, str | None] = {}
        self.stack: list[str | None] = []  # pushd / Push-Location

    def copy(self) -> "Scope":
        other = Scope(None)
        other.cwd, other.origin, other.vars, other.stack = self.cwd, self.origin, dict(self.vars), list(self.stack)
        return other

    def expand(self, text: str) -> str | None:
        """Substitute known variables; None when one is unknown or a subexpression remains."""
        unknown = False

        def rep(m: re.Match) -> str:
            nonlocal unknown
            name = next(g for g in m.groups() if g)
            key = name.lower()
            if key in self.vars:
                val = self.vars[key]
            elif key == "pwd" and self.cwd:
                val = self.cwd
            else:
                val = env_value(name)
            if val is None:
                unknown = True
                return m.group(0)
            return val

        out = VAR_RE.sub(rep, text)
        if unknown or SUBST in out or "${" in out or "$(" in out or "`" in out:
            return None
        if out.startswith("~"):
            out = os.path.expanduser("~") + out[1:]
        return out

    def resolve(self, raw: str) -> str | None:
        """Absolute normalised path for a target word, or None when it cannot be known."""
        if EXPRESSION.match(raw.strip()):
            return None
        text = self.expand(raw.strip())
        return None if text is None else self.literal(text)

    def literal(self, text: str) -> str | None:
        """Absolute normalised path of a path taken as it is (a file tool's path has no variables)."""
        text = text.strip()
        if not text:
            return None
        if is_absolute(text):
            return norm(text)
        return norm(self.cwd + "/" + text) if self.cwd is not None else None

    def cwd_protected(self) -> bool:
        """In the vault, a worktree or a store; an unknown folder counts as where it started."""
        here = self.cwd if self.cwd is not None else self.origin
        return here is not None and protected(here)

    def step(self, seg: str) -> bool:
        """Follow a `cd` or an assignment; True when the segment did only that."""
        m = CD_RE.match(seg)
        if m:
            if m.group(1).lower() in ("pushd", "push-location"):
                self.stack.append(self.cwd)
            toks = [t for t in tokenize(flat_redirects(m.group(2)))]
            if not toks:
                self.cwd = norm(os.path.expanduser("~"))
            else:
                self.cwd = None if toks[0].value == "-" else self.resolve(toks[0].value)
            return True
        if POP_RE.match(seg):
            self.cwd = self.stack.pop() if self.stack else None
            return True
        m = PS_ASSIGN.match(seg)
        if m:
            toks = tokenize(m.group(3))
            if m.group(2) == "=" and len(toks) == 1 and not toks[0].text.startswith(("(", "{", "@", "&")):
                self.vars[m.group(1).lower()] = self.expand(toks[0].value)
                return not re.match(r"[A-Za-z]+-[A-Za-z]+$", toks[0].text)  # `$x = Get-Date` runs a command
            self.vars[m.group(1).lower()] = None  # value of a command: unknown, and the
            return False                           # command itself is still checked
        m = CMD_SET.match(seg)
        if m:
            self.vars[m.group(1).lower()] = decode(m.group(2)).strip().strip('"')
            return True
        toks = tokenize(seg)
        if toks and toks[0].value.lower() in ("export", "local", "declare", "readonly"):
            toks = [t for t in toks[1:] if not t.value.startswith("-")]
        if toks and all(ENV_ASSIGN.match(t.value) and not t.text.startswith(("'", '"')) for t in toks):
            for t in toks:
                name, _, val = t.value.partition("=")
                self.vars[name.lower().rstrip("+")] = None if name.endswith("+") else self.expand(val)
            return True
        return False


class Simple:
    """One simple command of a call."""

    __slots__ = ("scope", "cwd", "text", "shell", "program", "toks", "k", "args")

    def __init__(self, scope: Scope, text: str, shell: str | None, toks: list[Tok], k: int) -> None:
        self.scope, self.cwd, self.text, self.shell = scope, scope.cwd, text, shell
        self.toks, self.k = toks, k
        self.program = program_name(toks[k].value) if k < len(toks) else ""
        self.args = toks[k + 1:]


def flat_redirects(seg: str) -> str:
    """`D:/x > $null 2>&1` -> `D:/x`: a `cd` operand without its redirections."""
    i = 0
    while i < len(seg):
        if seg[i] in "'\"":
            i = _skip_quoted(seg, i, seg[i])
            continue
        if seg[i] == ">":
            return re.sub(r"[\d*&]$", "", seg[:i])
        i += 1
    return seg


def redirect_targets(seg: str) -> list[str]:
    """Files written by `>` / `>>` outside quotes and brackets (`2>&1`, `>&2`, `> /dev/null`,
    `>( … )` and the comparisons of `[[ … ]]` skipped)."""
    if re.match(r"\s*(?:\[\[|\(\()", seg):
        return []
    seg = flat(seg)
    out: list[str] = []
    i, n = 0, len(seg)
    while i < n:
        c = seg[i]
        if c in "'\"":
            i = _skip_quoted(seg, i, c)
            continue
        if c == ">":
            j = i + 1
            while j < n and seg[j] in ">|":
                j += 1
            if j < n and seg[j] in "&(":
                i = j + 1
                continue
            found = next_word(seg, j)
            if found:
                if not found[0].text.startswith((">(", "<(")):  # process substitution
                    out.append(found[0].value)
                i = found[1]
                continue
            i = j
            continue
        i += 1
    return [t for t in out if t.lower() not in NOT_FILES]


def file_words(t: Tok) -> list[str]:
    """The paths of one word: `a.md,b.md` is two, "a, b.md" is one."""
    return [t.value] if t.quoted else [p for p in t.value.split(",") if p.strip()]


def ps_param(t: Tok) -> tuple[str, str | None] | None:
    """(name, value after `:`) of a PowerShell parameter word, or None."""
    if not t.text.startswith("-") or len(t.value) < 2 or not t.value[1].isalpha():
        return None
    name, colon, value = t.value[1:].partition(":")
    return name.lower(), value if colon else None


def ps_text_targets(args: list[Tok]) -> list[str]:
    """The file (or comma list of files) a Set-Content / Add-Content / Out-File / Tee-Object /
    Export-Csv call writes; a comma inside a quoted path belongs to the path."""
    i, first, target = 0, None, None
    while i < len(args):
        t = args[i]
        i += 1
        param = ps_param(t)
        if param:
            name, value = param
            if name in ("whatif", "wi") and value != "$false":
                return []
            if any(p.startswith(name) for p in PS_PATH_PARAMS):
                if value is not None:
                    target = [value]
                else:
                    target = file_words(args[i]) if i < len(args) else []
                    i += 1
            elif value is None and not any(s.startswith(name) for s in PS_SWITCHES):
                i += 1  # a parameter with a value: -Value, -Encoding, -Variable
            continue
        if t.text.startswith((">", "2>", "*>", "3>")):
            break
        if first is None:
            first = file_words(t)
    return (target if target is not None else first) or []


def written_files(c: Simple, text_only: bool = False) -> list[tuple[str, str]]:
    """(word as typed, normalised path) of each file a simple command changes.

    `text_only`: only files it gives new text (redirections, tee, Set-Content, Out-File, …);
    otherwise also the ones it copies, moves, creates or deletes.
    """
    words = list(redirect_targets(c.text))
    ps_tee = c.program == "tee" and (c.shell == "powershell" or any(
        (ps_param(t) or ("",))[0] in ("filepath", "variable", "literalpath", "inputobject") for t in c.args))
    if text_only and (c.program in PS_TEXT_WRITERS or ps_tee):
        words += ps_text_targets(c.args)
    elif c.program in (TEXT_WRITERS if text_only else WRITERS):
        for t in c.args:
            if t.text.startswith("-") and len(t.value) > 1 or re.match(r"[\d*&]?>", t.text):
                value = (ps_param(t) or ("", None))[1]
                words += [value] if value else []
            else:
                words += file_words(t)
    resolved = ((w, c.scope.resolve(w)) for w in words)
    return [(w, path) for w, path in resolved if path]


def walk(cmd: str, cwd: str | None, shell: str | None = None):
    """Yield each simple command that `cmd` runs (see the module docstring)."""
    yield from _walk(normalise(cmd, shell), Scope(cwd), shell, 0, [MAX_COMMANDS])


def _walk(text: Normalised, scope: Scope, shell: str | None, depth: int, budget: list[int]):
    if depth > MAX_DEPTH:
        return
    previous: Simple | None = None
    for a, b in split_segments(text.text):
        if budget[0] <= 0:
            return
        seg = text.text[a:b]
        here = [x._replace(pos=x.pos - a) for x in text.bodies if a <= x.pos < b or x.pos == b == len(text.text)]
        held: list[tuple[int, str]] = groups(seg)
        for body in here:  # `$( )` and heredocs that stand directly in this command
            if not any(s <= body.pos < s + len(g) for s, g in held):
                yield from _walk(normalise(body.text, body.shell), scope.copy(), body.shell, depth + 1, budget)
        for start, g in held:
            inside = [x._replace(pos=x.pos - start) for x in here if start <= x.pos < start + len(g)]
            yield from _walk(Normalised(g, inside), scope.copy(), shell, depth + 1, budget)
        seg = strip_keywords(seg, shell)
        if scope.step(seg):
            previous = None
            continue
        seg = drop_assignment(seg)
        toks = tokenize(seg)
        k = skip_prefixes(toks)
        simple = Simple(scope, seg, shell, toks, k)
        budget[0] -= 1
        yield simple
        if k < len(toks):
            inner = unwrap(seg, toks, k, len(seg), shell) or _piped(text.text[:a], simple, previous)
            if inner is not None and inner.text.strip() and not (inner.canonical and inner.same):
                sub = scope if inner.same else scope.copy()
                if inner.cwd:
                    sub.cwd = sub.resolve(inner.cwd)
                script = Normalised(inner.text, []) if inner.canonical else normalise(inner.text, inner.shell)
                yield from _walk(script, sub, inner.shell, depth + 1, budget)
        previous = simple


def _piped(before: str, c: Simple, previous: Simple | None):
    """`echo 'script' | bash`, `'script' | iex`: the script the command reads from the pipe."""
    from tach_lenh import Inner

    if previous is None or not before.rstrip(" \t\n").endswith("|") or before.rstrip(" \t\n").endswith("||"):
        return None
    if c.program in SH_SHELLS:
        shell, same = "bash", False
    elif c.program in PS_SHELLS | IEX_NAMES:
        shell, same = "powershell", c.program in IEX_NAMES
    else:
        return None
    if any(not t.value.startswith("-") for t in c.args):
        return None
    if previous.program in ("echo", "printf", "write-output", "write-host"):
        words = [t.value for t in previous.args if t.quoted or not t.value.startswith("-")]
    elif len(previous.toks) == 1 and previous.toks[0].quoted:
        words = [previous.toks[0].value]
    else:
        return None
    return Inner("\n".join(words), shell, same=same) if words else None
