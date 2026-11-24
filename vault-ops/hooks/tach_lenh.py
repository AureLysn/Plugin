#!/usr/bin/env python3
"""Shared command reading for the hooks (`tach_lenh` = split the command).

Why (plugin-benchmark-20261124 N1, executed 2026-11-24): every hook replaced quoted strings
with "" before it looked for its command, so a command handed to another program vanished.
None of these reached a hook: `bash -c "git reset --hard"`, `powershell -Command "git add -A"`,
`pwsh -c 'git push --force'`, `cmd /c git clean -fdx`,
`& "C:\\Program Files\\Git\\cmd\\git.exe" reset --hard`,
`Start-Process git -ArgumentList 'reset','--hard'`, `time git branch -D old`. The review of the
rule engine (V2, same day) showed the other side: comments, here-strings and the other shell's
quotes were read as commands, and one-line `for … do` bodies and continued lines were not.

`normalise(cmd, shell)` reads the text as its shell does (`bash`, `powershell`, `cmd`, or None when
unknown) and writes it in one simple form: comments dropped, continued lines joined, heredoc
bodies removed, and every quoted string or here-string inert: no character inside it can be
taken for syntax (`Tok.value` gives the real text back). The bodies of `$( … )`, of backticks
and of heredocs fed to a shell are listed apart, with the place they belong to.

`variants(cmd, shell)` returns the normalised command first, then rewritten copies; a hook runs
its own check on each:
  - a wrapper is replaced in place by the command it runs (`bash -c "X"` -> `X`), so a `cd`
    before it still applies: sh-family `-c` and here-strings, PowerShell `-Command`,
    `-EncodedCommand` and a positional script, `cmd /c` and `/k`, `Invoke-Expression`, `eval`,
    `Start-Process` and `{ script blocks }`;
  - launcher prefixes are dropped (`&`, `env`, `time`, `nohup`, `exec`, `command`, `sudo`,
    `nice`, `xargs`, `timeout`, `wsl`, `uv run`, `VAR=value`), and a quoted or path-qualified `git`
    (`"C:\\...\\git.exe"`, `git.exe`) becomes `git`; so are the Bash words that only lead a
    command (`if`, `then`, `do`, `else`, `while`, `!`, …);
  - the bodies listed apart, and those of `( … )` subshells and `{ … }` blocks, are added as
    separate variants.
Text that is only data (a commit message, an `echo` argument, a comment, a here-string, a heredoc
fed to `cat`, a single-quoted string) is never unwrapped. `duong_dan.walk` goes through the same
forms one simple command at a time, with its shell and working directory.

Not covered: `python -c` / `node -e` bodies, commands built from variables (`& $git reset`),
`cmd /s /c` quoting, scripts run from files (`bash x.sh`, `-File`). Any internal error
returns `[cmd]`, which is how the hooks behaved before this module (git-guard < 0.8.0).

`shell_of(payload)` names the shell of the tool; the hooks read their payload as UTF-8 bytes,
because Python would decode stdin with the console code page (cp1252 here) and garble Vietnamese.
`unreadable(reason)` is the shared fail mode (plugin-benchmark-20261124 G4): input a hook
cannot read is allowed by default (fail open, as documented since 2026-11-23); with
`GIT_GUARD_STRICT=1` in the environment the hook blocks it instead and says why.
"""

from __future__ import annotations

import base64
import os
import re
import sys
from typing import NamedTuple

STRICT_ENV = "GIT_GUARD_STRICT"

MAX_DEPTH = 6
MAX_VARIANTS = 80
MAX_HEREDOCS = 20  # heredocs that start on one line

ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\+?=")

SH_SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "ash"}
PS_SHELLS = {"powershell", "pwsh", "powershell_ise"}
CMD_SHELLS = {"cmd"}
IEX_NAMES = {"invoke-expression", "iex", "eval"}
START_NAMES = {"start-process", "saps", "start"}

# Launcher words that run the next word as the command -> their options that take a value.
PREFIX_OPTS: dict[str, set[str]] = {
    "&": set(), "command": set(), "builtin": set(), "exec": set(), "time": set(),
    "nohup": set(), "noglob": set(), "winpty": set(),
    "env": {"-u", "--unset", "-C", "--chdir"},
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-U"},
    "nice": {"-n", "--adjustment"},
    "stdbuf": {"-i", "-o", "-e"},
    "xargs": {"-n", "-L", "-P", "-I", "-d", "-E", "-s", "-a", "--max-args", "--max-procs",
              "--delimiter", "--arg-file", "--max-lines", "--replace"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
    "wsl": {"-d", "--distribution", "-u", "--user", "--cd"},
}
RUN_PREFIXES = {"uv", "poetry", "pipenv", "pdm"}  # `uv run python x.py`
# Bash words that only lead the command after them.
KEYWORDS = re.compile(r"^\s*(?:(?:if|elif|then|else|do|while|until|coproc|!)(?=[\s(]|$)\s*|\{(?=\s)\s*)+")

# powershell.exe / pwsh parameters that take a value (full names and short aliases).
PS_VALUE_FULL = ("executionpolicy", "windowstyle", "workingdirectory", "configurationname",
                 "outputformat", "inputformat", "version", "psconsolefile", "settingsfile",
                 "custompipename", "encodedarguments")
PS_VALUE_ALIAS = {"ep", "ex", "w", "wd", "config", "of", "o", "if", "in", "v", "settings", "ea"}

# Start-Process parameters that take a value, other than -FilePath and -ArgumentList.
SP_VALUE_FULL = ("workingdirectory", "verb", "windowstyle", "redirectstandardoutput",
                 "redirectstandarderror", "redirectstandardinput", "credential", "environment")

# Inside a quoted word of normalised text these characters are written as private-use ones.
_PUA = 0xE100
_INERT = "'\"`;|&<>(){}\n#"
_ENC = {ord(c): chr(_PUA + ord(c)) for c in _INERT}
_DEC = {_PUA + ord(c): c for c in _INERT + " "}
_ESC_SPACE = chr(_PUA + ord(" "))
SUBST = chr(0xE0FF)  # stands for a `$( … )` or backtick substitution
_DROP = {**{k: None for k in _DEC}, ord(SUBST): None, 0: None}

_HEREDOC_START = re.compile(r"<<(-?)[ \t]*(?:'([^'\n]+)'|\"([^\"\n]+)\"|(\\?)([A-Za-z_][\w.-]*))")
_HERE_START = re.compile(r"@(['\"])[ \t]*\n")


def decode(text: str) -> str:
    """The text a piece of normalised text stands for."""
    return text.translate(_DEC)


class Tok:
    """One word of a command: absolute position, raw text, value with quotes removed."""

    __slots__ = ("start", "end", "text", "value", "quoted")

    def __init__(self, start: int, end: int, text: str, value: str, quoted: bool) -> None:
        self.start, self.end, self.text, self.value, self.quoted = start, end, text, value, quoted


class Body(NamedTuple):
    """A script inside a command: where it stands in the normalised text, its text, its shell."""
    pos: int
    text: str
    shell: str | None


class Normalised(NamedTuple):
    text: str
    bodies: list[Body]


class Inner(NamedTuple):
    """What a wrapper runs. `canonical`: already normalised. `same`: in the current shell (eval,
    iex, a script block). `cwd`: the folder it starts in, when given (Start-Process)."""
    text: str
    shell: str | None
    canonical: bool = False
    same: bool = False
    cwd: str | None = None


# --------------------------------------------------------------------- reading one shell's text

class _Reader:
    """Cursor over a command as typed; methods take an index and return the index after it."""

    def __init__(self, s: str, shell: str | None) -> None:
        self.s, self.n, self.shell = s, len(s), shell
        self.found: list[str] = []  # substitution bodies met inside the last string

    def _closes(self, j: int) -> bool:
        """Unknown shell: does a quote before index j look like a closing one (`"D:\\dir\\" |`)?"""
        return j >= self.n or self.s[j] in " \t\n;|),"

    def single(self, i: int) -> tuple[str, int]:
        s, j, buf = self.s, i + 1, []
        while j < self.n:
            if s[j] == "'":
                if self.shell in ("powershell", None) and s[j + 1:j + 2] == "'":
                    buf.append("'")
                    j += 2
                    continue
                break
            buf.append(s[j])
            j += 1
        return "".join(buf), j + 1

    def ansi_c(self, i: int) -> tuple[str, int]:
        """Bash $'…' with s[i] == "'" (the dollar sign is already passed)."""
        s, j, buf = self.s, i + 1, []
        while j < self.n and s[j] != "'":
            if s[j] == "\\" and j + 1 < self.n:
                buf.append({"n": "\n", "t": "\t"}.get(s[j + 1], s[j + 1]))
                j += 2
                continue
            buf.append(s[j])
            j += 1
        return "".join(buf), j + 1

    def double(self, i: int) -> tuple[str, int]:
        s, j, buf = self.s, i + 1, []
        ps, cmd = self.shell == "powershell", self.shell == "cmd"
        while j < self.n:
            c, nxt = s[j], s[j + 1:j + 2]
            if c == '"':
                if self.shell in ("powershell", None) and nxt == '"':
                    buf.append('"')
                    j += 2
                    continue
                break
            if c == "\\" and not ps:
                if nxt == '"':
                    if (self.shell is None or cmd) and self._closes(j + 2):
                        buf.append("\\")  # "D:\dir\" : the backslash is the last character
                        j += 1
                        break
                    buf.append('"')
                    j += 2
                    continue
                if nxt == "\n" and not cmd:
                    j += 2
                    continue
                if nxt and nxt in "$`\\" and not cmd:
                    buf.append(c + nxt)
                    j += 2
                    continue
                buf.append(c)
                j += 1
                continue
            if c == "`" and not cmd:
                if self.shell == "bash":
                    end = self.backtick(j)
                    self.found.append(s[j + 1:end - 1])
                    buf.append(SUBST)
                    j = end
                    continue
                buf.append('"' if nxt == '"' else " ")
                j += 2
                continue
            if c == "$" and nxt == "(" and not cmd:
                end = self.close(j + 1)
                if s[j + 2:j + 3] != "(" or ps:  # not $(( arithmetic ))
                    self.found.append(s[j + 2:end - 1])
                buf.append(SUBST)
                j = end
                continue
            buf.append(c)
            j += 1
        return "".join(buf), j + 1

    def here_string(self, i: int) -> tuple[str, int] | None:
        """PowerShell @'…'@ or @"…"@ with s[i] == "@"."""
        m = _HERE_START.match(self.s, i)
        if not m:
            return None
        q = m.group(1)
        end = self.s.find("\n" + q + "@", m.end() - 1)
        body, after = (self.s[m.end():], self.n) if end < 0 else (self.s[m.end():max(end, m.end())], end + 3)
        if q == '"':
            self.found += _substitution_texts(body, "powershell")
        return body, after

    def backtick(self, i: int) -> int:
        j = i + 1
        while j < self.n and self.s[j] != "`":
            j += 2 if self.s[j] == "\\" else 1
        return min(j + 1, self.n)

    def skip_string(self, i: int) -> int:
        return self.single(i)[1] if self.s[i] == "'" else self.double(i)[1]

    def close(self, i: int) -> int:
        """s[i] opens a bracket: index just past the one that closes it."""
        opener = self.s[i]
        closer = {"(": ")", "{": "}"}[opener]
        depth, j, pending = 0, i, []
        saved, self.found = self.found, []
        try:
            while j < self.n:
                c = self.s[j]
                if c == "'" and self.shell != "cmd":
                    j = self.ansi_c(j)[1] if self.s[j - 1:j] == "$" and self.shell == "bash" else self.single(j)[1]
                    continue
                if c == '"':
                    j = self.double(j)[1]
                    continue
                if c == "@" and self.shell != "bash":
                    here = self.here_string(j)
                    if here:
                        j = here[1]
                        continue
                if c == "\\" and self.shell == "bash":
                    j += 2
                    continue
                if c == "`":
                    j = self.backtick(j) if self.shell == "bash" else j + 2
                    continue
                if c == "#" and self.shell != "cmd" and self.s[j - 1:j] in (" ", "\t", "\n", ";", "("):
                    nl = self.s.find("\n", j)
                    j = self.n if nl < 0 else nl
                    continue
                if c == "<" and self.shell != "powershell":
                    doc = self.heredoc(j)
                    if doc:
                        pending.append(doc)
                        j = doc[4]
                        continue
                if c == "\n" and pending:
                    j += 1
                    for doc in pending:
                        j = self.heredoc_body(j, doc)[1]
                    pending = []
                    continue
                if c == opener:
                    depth += 1
                elif c == closer:
                    depth -= 1
                    if depth == 0:
                        return j + 1
                j += 1
            return self.n
        finally:
            self.found = saved

    def heredoc(self, i: int) -> tuple[str, bool, bool, str, int] | None:
        """(delimiter, tabs stripped, quoted, text as typed, index after) of a heredoc start."""
        if self.s[i:i + 2] != "<<" or self.s[i:i + 3] == "<<<" or self.s[i - 1:i] == "<":
            return None
        m = _HEREDOC_START.match(self.s, i)
        if not m:
            return None
        delim = m.group(2) or m.group(3) or m.group(5)
        quoted = bool(m.group(2) or m.group(3) or m.group(4))
        if self.shell != "bash" and not re.compile(r"^\t*" + re.escape(delim) + r"$", re.M).search(self.s, m.end()):
            return None  # unknown shell: only with a closing line
        return delim, m.group(1) == "-", quoted, m.group(0), m.end()

    def heredoc_body(self, i: int, doc: tuple) -> tuple[str, int]:
        """(body, index after the closing line) when the body starts at i."""
        delim, tabs, lines = doc[0], doc[1], []
        while i < self.n:
            nl = self.s.find("\n", i)
            line, nxt = (self.s[i:], self.n) if nl < 0 else (self.s[i:nl], nl + 1)
            if (line.lstrip("\t") if tabs else line) == delim:
                return "\n".join(lines), nxt
            lines.append(line)
            i = nxt
        return "\n".join(lines), self.n


def _substitution_texts(text: str, shell: str | None) -> list[str]:
    """Bodies of `$( … )` (and Bash backticks) in unquoted text, as in an unquoted heredoc."""
    out, r, i = [], _Reader(text, shell), 0
    while i < len(text):
        if text[i] == ("\\" if shell != "powershell" else "`"):
            i += 2
        elif text.startswith("$(", i) and (shell == "powershell" or not text.startswith("$((", i)):
            end = r.close(i + 1)
            out.append(text[i + 2:end - 1])
            i = end
        elif text[i] == "`" and shell == "bash":
            end = r.backtick(i)
            out.append(text[i + 1:end - 1])
            i = end
        else:
            i += 1
    return out


def _skip_blanks(s: str, i: int) -> int:
    while s[i:i + 1] in (" ", "\t"):
        i += 1
    return i


def normalise(cmd: str, shell: str | None = None) -> Normalised:
    """`cmd` in the simple form described in the module docstring."""
    s = cmd.translate(_DROP).replace("\r\n", "\n")
    r = _Reader(s, shell)
    out: list[str] = []
    bodies: list[Body] = []
    pending: list[tuple[tuple, int, str]] = []  # (heredoc, its position, program it is fed to)
    bash, ps, dos = shell == "bash", shell == "powershell", shell == "cmd"
    size, i, n, prev, line = 0, 0, len(s), "\n", 0  # line: index in `out` where this line starts

    def put(t: str) -> None:
        nonlocal size, prev
        if t:
            out.append(t)
            size += len(t)
            prev = t[-1]

    def put_string(q: str, text: str) -> None:
        if text.endswith("\\"):
            text = text[:-1] + "/"
        bodies.extend(Body(size, b, shell) for b in r.found)
        r.found = []
        put(q + text.translate(_ENC) + q)

    while i < n:
        c, nxt = s[i], s[i + 1:i + 2]
        if c == "\n":
            if pending:
                text = "".join(out[line:])
                last = _last_program(text) if "|" in text else ""
                for doc, pos, program in pending:
                    body, after = r.heredoc_body(i + 1, doc)
                    i = after - 1
                    if program not in SH_SHELLS | PS_SHELLS and last:
                        program = last  # cat <<EOF | bash
                    if program in SH_SHELLS | PS_SHELLS:
                        bodies.append(Body(pos, body, "bash" if program in SH_SHELLS else "powershell"))
                    elif not doc[2]:
                        bodies.extend(Body(pos, b, "bash") for b in _substitution_texts(body, "bash"))
                pending = []
            put("\n")
            line = len(out)
            i += 1
        elif c == "#" and not dos and (prev in " \t\n;|&()" or prev == "," and not bash):
            nl = s.find("\n", i)
            i = n if nl < 0 else nl
        elif c == "<" and nxt == "#" and not bash and not dos:
            end = s.find("#>", i + 2)
            put(" ")
            i = n if end < 0 else end + 2
        elif c == "@" and not bash and not dos and _HERE_START.match(s, i):
            text, i = r.here_string(i)
            put_string("'", text)
        elif c == "'":
            if dos:
                put(c.translate(_ENC))
                i += 1
            else:
                text, i = r.single(i)
                put_string("'", text)
        elif c == '"':
            text, i = r.double(i)
            put_string('"', text)
        elif c == "$" and nxt == "'" and not ps and not dos:
            text, i = r.ansi_c(i + 1)
            put_string("'", text)
        elif c == "$" and nxt == "(" and not dos:
            end = r.close(i + 1)
            if s[i + 2:i + 3] != "(" or ps:
                bodies.append(Body(size, s[i + 2:end - 1], shell))
            put(SUBST)
            i = end
        elif c == "$" and nxt == "{":
            end = r.close(i + 1)
            inner = s[i + 2:end - 1]
            bodies.extend(Body(size, b, shell) for b in _substitution_texts(inner, shell))
            put("$" + ("{" + inner + "}").translate(_ENC))
            i = end
        elif c == "`" and bash:
            end = r.backtick(i)
            bodies.append(Body(size, s[i + 1:end - 1], shell))
            put(SUBST)
            i = end
        elif c == "`" and not dos and nxt == "\n":
            put(" ")
            i = _skip_blanks(s, i + 2)
        elif c == "`" and shell is None and not nxt.isspace() and s.find("`", i + 1) > i:
            end = r.backtick(i)  # unknown shell: a pair of backticks is read as Bash does
            bodies.append(Body(size, s[i + 1:end - 1], shell))
            put(SUBST)
            i = end
        elif c == "`" and not dos:
            put(nxt.translate(_ENC))
            i += 2
        elif c == "\\" and not ps and not dos and nxt == "\n":
            put(" ")
            i = _skip_blanks(s, i + 2)
        elif c == "\\" and not ps and not dos and nxt and nxt in "'\"":
            put(nxt.translate(_ENC))
            i += 2
        elif c == "\\" and bash and nxt == " ":
            put(_ESC_SPACE)
            i += 2
        elif c == "\\" and bash and nxt and nxt in ";|&<>(){}#`":
            put(nxt.translate(_ENC))
            i += 2
        elif c == "^" and dos:
            put(" " if nxt == "\n" else nxt.translate(_ENC))
            i += 2
        elif c == "<" and nxt == "<" and not ps and not dos and len(pending) < MAX_HEREDOCS and r.heredoc(i):
            doc = r.heredoc(i)
            pending.append((doc, size, _last_program("".join(out[line:]))))
            put("<<'" + doc[0].translate(_ENC) + "'")
            i = doc[4]
        else:
            put(c)
            i += 1
    return Normalised("".join(out), bodies)


# --------------------------------------------------------------------- normalised text

def _skip_quoted(s: str, i: int, q: str) -> int:
    """Index just past the quote that closes the one at s[i] (end of string if unclosed)."""
    j = s.find(q, i + 1)
    return len(s) if j < 0 else j + 1


def _match_paren(s: str, i: int) -> int:
    """s[i] is "(" or "{": index just past its matching closer, skipping quoted text."""
    opener = s[i]
    closer = ")" if opener == "(" else "}"
    depth, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"":
            i = _skip_quoted(s, i, c)
            continue
        if c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def next_word(s: str, i: int) -> tuple[Tok, int] | None:
    """The word that starts at or after i, and the index after it."""
    n = len(s)
    while i < n and s[i].isspace():
        i += 1
    if i >= n:
        return None
    start, val, quoted, depth = i, [], False, 0
    while i < n:
        c = s[i]
        if c.isspace() and depth == 0:
            break
        if c in "'\"":
            quoted = True
            end = _skip_quoted(s, i, c)
            val.append(s[i + 1:end - 1] if end - 1 > i and s[end - 1] == c else s[i + 1:end])
            i = end
            continue
        if c in "{(":
            depth += 1
        elif c in "})" and depth:
            depth -= 1
        val.append(c)
        i += 1
    return Tok(start, i, s[start:i], decode("".join(val)), quoted), i


def tokenize(s: str, base: int = 0) -> list[Tok]:
    """Split on whitespace outside quotes and `{ }` / `( )`; positions are offset by `base`."""
    toks: list[Tok] = []
    found = next_word(s, 0)
    while found:
        t, i = found
        t.start, t.end = t.start + base, t.end + base
        toks.append(t)
        found = next_word(s, i)
    return toks


def split_segments(s: str) -> list[tuple[int, int]]:
    """Spans of simple commands, split on ; && || | & and newlines outside quotes, ( ) and { }.

    `2>&1`, `&>` and `>|` are redirections, not separators. A PowerShell call operator `&` at the
    start of a segment also splits; the path after it then becomes the segment's first word.
    """
    spans: list[tuple[int, int]] = []
    start, i, n, depth = 0, 0, len(s), 0
    while i < n:
        c = s[i]
        if c in "'\"":
            i = _skip_quoted(s, i, c)
            continue
        if c in "({":
            depth += 1
        elif c in ")}":
            depth = max(0, depth - 1)
        elif depth == 0 and c in ";|&\n":
            before = s[i - 1:i]
            if c == "&" and (before in (">", "<") or s[i + 1:i + 2] == ">") or c == "|" and before == ">":
                i += 1
                continue
            spans.append((start, i))
            j = i + 1
            while j < n and s[j] in ";|&":
                j += 1
            start = i = j
            continue
        i += 1
    spans.append((start, n))
    return [(a, b) for a, b in spans if s[a:b].strip()]


def program_name(word: str) -> str:
    """`"C:\\Program Files\\Git\\cmd\\git.exe"` -> `git`; `/usr/bin/bash` -> `bash`."""
    base = re.split(r"[\\/]", word.strip())[-1].lower()
    return base[:-4] if base.endswith(".exe") else base


def skip_prefixes(toks: list[Tok]) -> int:
    """Index of the word that is actually run, after `VAR=value` and launcher prefixes."""
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if ENV_ASSIGN.match(t.value) and not t.text.startswith(("'", '"')):
            i += 1
            continue
        word = t.value.lower()
        if not t.quoted and word in RUN_PREFIXES and i + 1 < n and toks[i + 1].value == "run":
            i += 2
            while i < n and toks[i].value.startswith("-"):
                i += 1
            continue
        if t.quoted or word not in PREFIX_OPTS:
            break
        takes_value = PREFIX_OPTS[word]
        i += 1
        while i < n and not toks[i].quoted and toks[i].value.startswith("-") and len(toks[i].value) > 1:
            opt = toks[i].value
            i += 1
            if opt == "--":
                break
            if opt in takes_value and i < n:
                i += 1
        if word == "timeout" and i < n and re.match(r"\d", toks[i].value):
            i += 1
    return i


def strip_keywords(seg: str, shell: str | None) -> str:
    """`do git add -A` -> `git add -A` (Bash words that only lead a command)."""
    m = KEYWORDS.match(seg) if shell != "powershell" else None
    return seg[m.end():] if m else seg


def _last_program(text: str) -> str:
    spans = split_segments(text)
    if not spans:
        return ""
    toks = tokenize(strip_keywords(text[spans[-1][0]:spans[-1][1]], None))
    k = skip_prefixes(toks)
    return program_name(toks[k].value) if k < len(toks) else ""


def groups(s: str) -> list[tuple[int, str]]:
    """(offset, body) of each outermost `( … )` and `{ … }` outside quotes. `${x}`, `@{ … }`,
    `stash@{1}`, `a{b,c}` and empty ones are not bodies; a PowerShell `@( … )` is."""
    out: list[tuple[int, str]] = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"":
            i = _skip_quoted(s, i, c)
        elif c in "({":
            before, end = s[i - 1:i], _match_paren(s, i)
            body = s[i + 1:end - 1] if s[end - 1:end] == (")" if c == "(" else "}") and end - 1 > i else s[i + 1:end]
            if body.strip() and (c == "(" or not (before in ("$", "@") or re.match(r"[\w.,/*-]", before))):
                out.append((i + 1, body))
            i = end
        else:
            i += 1
    return out


def flat(s: str) -> str:
    """`s` with the inside of `( … )` and `{ … }` blanked (positions kept)."""
    for start, body in groups(s):
        s = s[:start] + " " * len(body) + s[start + len(body):]
    return s


# --------------------------------------------------------------------- wrappers

def _script(s: str, toks: list[Tok], j: int, end: int, shell: str | None) -> Inner | None:
    """The script given from word j on: one word -> its value (or block body), else raw text."""
    if j >= len(toks):
        return None
    if j == len(toks) - 1:
        t = toks[j]
        if t.text.startswith("{") and t.text.endswith("}"):
            return Inner(t.text[1:-1], shell, canonical=True)
        return Inner(t.value, shell)
    return Inner(s[toks[j].start:end], shell, canonical=True)


def _decode_ps(b64: str) -> str | None:
    try:
        return base64.b64decode(b64 + "=" * (-len(b64) % 4)).decode("utf-16-le")
    except Exception:
        return None


def _sh_inner(s: str, toks: list[Tok], i: int, end: int) -> Inner | None:
    j, has_c = i + 1, False
    while j < len(toks):
        t, v = toks[j], toks[j].value
        if t.quoted or not v.startswith(("-", "+")) or v in ("-", "+"):
            break
        j += 1
        if v == "--":
            break
        if v.startswith("--"):
            if v in ("--rcfile", "--init-file"):
                j += 1
            continue
        if v[1:] in ("o", "O"):
            j += 1
            continue
        if "c" in v[1:]:
            has_c = True
    if has_c and j < len(toks):
        return Inner(toks[j].value, "bash")
    for k in range(i + 1, len(toks)):  # here-string: bash <<< "script"
        if toks[k].text == "<<<" and k + 1 < len(toks):
            return Inner(toks[k + 1].value, "bash")
        if toks[k].text.startswith("<<<") and len(toks[k].text) > 3:
            return Inner(toks[k].value[3:], "bash")
    return None


def _ps_takes_value(name: str) -> bool:
    return name in PS_VALUE_ALIAS or (len(name) >= 2 and any(p.startswith(name) for p in PS_VALUE_FULL))


def _ps_inner(s: str, toks: list[Tok], i: int, end: int) -> Inner | None:
    j = i + 1
    while j < len(toks):
        t, v = toks[j], toks[j].value
        if not t.quoted and len(v) > 1 and v[0] in "-/":
            name = v.lstrip("-/").lower().split(":", 1)[0]
            if name and "command".startswith(name):
                return _script(s, toks, j + 1, end, "powershell")
            if name in ("e", "ec") or (len(name) >= 2 and "encodedcommand".startswith(name)):
                text = _decode_ps(toks[j + 1].value) if j + 1 < len(toks) else None
                return Inner(text, "powershell") if text else None
            if name and "file".startswith(name):
                return None  # a script file: its content is not on the command line
            j += 2 if _ps_takes_value(name) and ":" not in v else 1
            continue
        if t.text == "-" or t.text.startswith("<"):
            return None  # script read from stdin
        return _script(s, toks, j, end, "powershell")  # first positional argument starts the script
    return None


def _cmd_inner(s: str, toks: list[Tok], i: int, end: int) -> Inner | None:
    for j in range(i + 1, len(toks)):
        v = toks[j].value.lower()
        if v in ("/c", "/k", "/r", "//c", "//k", "//r"):  # Git Bash spells the switch with two slashes
            return _script(s, toks, j + 1, end, "cmd")
        if not v.startswith("/"):
            return None
    return None


def _iex_inner(s: str, toks: list[Tok], i: int, end: int) -> Inner | None:
    if program_name(toks[i].value) == "eval":
        text = " ".join(t.value for t in toks[i + 1:])
        return Inner(text, "bash", same=True) if text.strip() else None
    j = i + 1
    while j < len(toks):
        t, v = toks[j], toks[j].value
        if t.quoted or len(v) < 2 or not v.startswith("-"):
            break
        j += 1
        if "command".startswith(v.lstrip("-").lower()):
            break
    inner = _script(s, toks, j, end, "powershell")
    return inner._replace(same=True) if inner else None


def _arg_list(toks: list[Tok], j: int) -> tuple[str, int]:
    """Start-Process -ArgumentList value: `'a','b'`, `'a', 'b'`, `@('a','b')` or `"a b"` -> `a b`."""
    parts: list[str] = []
    while j < len(toks):
        t = toks[j]
        parts.append(t.value)
        j += 1
        if not (t.value.endswith(",") or (j < len(toks) and toks[j].text.startswith(","))):
            break
    joined = ",".join(parts)
    if joined.startswith("@(") and joined.endswith(")"):
        joined = joined[2:-1]
    items = [p for p in (x.strip() for x in joined.split(",")) if p]
    return " ".join(f'"{p}"' if " " in p and len(items) > 1 else p for p in items), j


def _start_inner(s: str, toks: list[Tok], i: int, end: int) -> Inner | None:
    word = toks[i].value.lower()
    params = [t.value.lstrip("-").lower() for t in toks[i + 1:] if not t.quoted and t.value.startswith("-")]
    ps_style = word != "start" or any(
        p and ("argumentlist".startswith(p) or "filepath".startswith(p) or p == "args") for p in params)
    if not ps_style:  # cmd: start ["title"] [/switches] command args
        j = i + 1
        if j < len(toks) and toks[j].quoted and j + 1 < len(toks):
            j += 1
        while j < len(toks) and toks[j].value.startswith("/"):
            j += 1
        return Inner(s[toks[j].start:end], "cmd", canonical=True) if j < len(toks) else None
    file: str | None = None
    args: str | None = None
    workdir: str | None = None
    j = i + 1
    while j < len(toks):
        t, v = toks[j], toks[j].value
        if not t.quoted and len(v) > 1 and v.startswith("-"):
            name = v.lstrip("-").lower().split(":", 1)[0]
            if name in ("path", "pspath", "lp") or (name and "filepath".startswith(name)):
                if j + 1 < len(toks):
                    file = toks[j + 1].value
                j += 2
                continue
            if name == "args" or (name and "argumentlist".startswith(name)):
                args, j = _arg_list(toks, j + 1)
                continue
            if len(name) >= 2 and "workingdirectory".startswith(name) and j + 1 < len(toks):
                workdir = toks[j + 1].value
            j += 2 if len(name) >= 2 and any(p.startswith(name) for p in SP_VALUE_FULL) else 1
            continue
        if file is None:
            file = v
            j += 1
        elif args is None:
            args, j = _arg_list(toks, j)
        else:
            j += 1
    if not file:
        return None
    head = "git" if program_name(file) == "git" else (f'"{file}"' if " " in file else file)
    return Inner(f"{head} {args}" if args else head, "cmd", cwd=workdir)


def unwrap(s: str, toks: list[Tok], k: int, end: int, shell: str | None) -> Inner | None:
    """What the command at toks[k] runs on behalf of its caller, or None."""
    word = toks[k]
    if word.text.startswith("{") and word.text.endswith("}"):
        return Inner(word.text[1:-1], shell, canonical=True, same=True)
    name = program_name(word.value)
    if name in SH_SHELLS:
        return _sh_inner(s, toks, k, end)
    if name in PS_SHELLS:
        return _ps_inner(s, toks, k, end)
    if name in CMD_SHELLS:
        return _cmd_inner(s, toks, k, end)
    if name in IEX_NAMES:
        return _iex_inner(s, toks, k, end)
    if name in START_NAMES:
        return _start_inner(s, toks, k, end)
    return None


# --------------------------------------------------------------------- variants

def _rewrite_once(text: str, shell: str | None) -> tuple[str | None, list[tuple[Normalised, str | None]]]:
    """`text` with each wrapper replaced by what it runs, and scripts found inside those."""
    repl: list[tuple[int, int, str]] = []
    extras: list[tuple[Normalised, str | None]] = []
    for a, b in split_segments(text):
        start = a
        a = b - len(strip_keywords(text[a:b], shell))
        toks = tokenize(text[a:b], a)
        k = skip_prefixes(toks)
        if k >= len(toks):
            continue
        word = toks[k]
        inner = unwrap(text, toks, k, b, shell)
        if inner is not None and inner.text.strip():
            if inner.canonical:
                new = inner.text
            else:
                n = normalise(inner.text, inner.shell)
                new = n.text
                extras += [(normalise(x.text, x.shell), x.shell) for x in n.bodies]
        elif program_name(word.value) == "git" and (k > 0 or word.text != "git"):
            new = "git" + text[word.end:b]
        elif a > start and text[start:a].strip():
            new = text[a:b]  # `do git add -A` -> `git add -A`
        else:
            continue
        if new.strip():
            left = start if text[start:a].strip() else toks[0].start
            repl.append((left, b, new.strip() + (" " if text[b - 1:b].isspace() else "")))
    if not repl:
        return None, extras
    out = text
    for a, b, new in sorted(repl, reverse=True):
        out = out[:a] + new + out[b:]
    return out, extras


def _collect(norm: Normalised, shell: str | None, depth: int, out: list[str]) -> None:
    if norm.text in out or len(out) >= MAX_VARIANTS or not norm.text.strip():
        return
    out.append(norm.text)
    if depth <= 0:
        return
    rewritten, extras = _rewrite_once(norm.text, shell)
    if rewritten is not None:
        _collect(Normalised(rewritten, []), shell, depth - 1, out)
    for n, sh in extras:
        _collect(n, sh, depth - 1, out)
    for body in norm.bodies:
        _collect(normalise(body.text, body.shell), body.shell, depth - 1, out)
    for _, body in groups(norm.text):
        _collect(Normalised(body, []), shell, depth - 1, out)


def variants(cmd: str, shell: str | None = None) -> list[str]:
    """The normalised command first, then each unwrapped form of it (see the module docstring)."""
    out: list[str] = []
    try:
        _collect(normalise(cmd, shell), shell, MAX_DEPTH, out)
    except Exception:
        return [cmd]
    return out or [cmd]


# --------------------------------------------------------------------- payload and fail mode

def shell_of(data: object) -> str | None:
    """The shell a payload's tool runs (None: another host, or not a shell tool)."""
    tool = str((data.get("tool_name") or data.get("toolName") or "") if isinstance(data, dict) else "").lower()
    return {"bash": "bash", "powershell": "powershell"}.get(tool)


def strict_mode() -> bool:
    return os.environ.get(STRICT_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def unreadable(reason: str, default: int = 0) -> int:
    """Exit code for input a hook cannot read or a check that failed (G4).

    Default: `default` — 0 (allow) for unreadable input, 1 (non-blocking error) when the
    check itself raised. With GIT_GUARD_STRICT=1: 2 (block), with the reason on stderr.
    """
    if strict_mode():
        print(
            f"CHẶN ({STRICT_ENV}=1): hook không đọc được lệnh ({reason}) nên chặn thay vì cho qua.\n"
            f"  Bỏ biến môi trường {STRICT_ENV} (hoặc đặt 0) để trở về mặc định: cho qua khi không đọc được.",
            file=sys.stderr,
        )
        return 2
    if default:
        print(f"hook: {reason} (không chặn)", file=sys.stderr)
    return default


if __name__ == "__main__":  # manual check: python tach_lenh.py "<command>" [bash|powershell|cmd]
    for v in variants(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None):
        print(repr(v))
