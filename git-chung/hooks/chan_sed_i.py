#!/usr/bin/env python3
"""PreToolUse hook (Bash): block `sed -i` / `sed --in-place`.

Git Bash `sed -i` strips CR (`\\r\\n` -> `\\n`) on Windows, so a small edit rewrites every line of a
CRLF file on disk (`01_Origine/05_Meta/Rules/global/ai-tool-and-environment-quirks.md`). The vault's
`.gitattributes` stores text as LF (`text eol=lf`), so `git diff` does not show that change — the
file's line endings move without a trace in the diff. (The text here said `* -text` until 2026-11-14;
that was never what the file declares.)

Exit 0 = allow, 2 = block.
"""

from __future__ import annotations

import json
import re
import sys

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", re.S)
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')

# Match sed with -i (including bundled short flags like -ri, -ni, -Ei or -i.bak) or --in-place
# `sed` may also be started by another command: `… | xargs sed -i …`, `find … -exec sed -i … \;`
# (the `xargs` case was a failing test case until 2026-11-14: the hook let it through).
SED_I = re.compile(
    r"(?:^|[;&|]\s*|\$\(\s*|`\s*)"
    r"(?:(?:xargs|find)\b[^\n;|&`)]*?\s)?"
    r"sed\b"
    r"[^\n;|&`)]*?"
    r"(?:\s-[A-Za-z]*i\S*|\s--in-place\b)"
)


def check(cmd: str) -> str | None:
    s = QUOTED.sub('""', HEREDOC.sub("", cmd))
    if SED_I.search(s):
        return (
            "CHẶN: không dùng `sed -i` (ai-tool-and-environment-quirks.md).\n"
            "  `sed -i` của Git Bash nuốt sạch CR trên file CRLF -> sửa 3 dòng mà\n"
            "  mọi dòng của file trên đĩa đều đổi. `.gitattributes` lưu chữ dạng LF\n"
            "  (`text eol=lf`) nên `git diff` không hiện thay đổi đó.\n"
            "  Cách đúng:\n"
            "    - Sửa 1 file: dùng công cụ `Edit`, HOẶC\n"
            "    - Sửa hàng loạt bằng Python: dùng `vaultlib.write_keep_eol(p, text)`\n"
            "      hoặc đọc/ghi bytes giữ nguyên `\\r\\n` / `\\n` của từng file."
        )
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    ti = data.get("tool_input") or data.get("toolInput") or {}
    cmd = ti.get("command") or ti.get("CommandLine") or ""
    msg = check(cmd)
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
