#!/usr/bin/env python3
"""PreToolUse hook (Bash): block branch switching (`git checkout <branch>`, `git switch`, `gh pr checkout`)
on a main tree of the vault (`D:\\AureLysn`, and the nested repositories `05_Evasion` and `04_Portfolio`).

Why: The main vault tree stays on `main` while Obsidian is open. Switching branches on the main
tree mutates files under Obsidian and collides with concurrent sessions. Parallel branch work must
use an external `git worktree` (see `git-an-toan`).
Single-file restoration (`git checkout -- <path>`, `git checkout HEAD -- <path>`) is allowed.

Exit 0 = allow, 2 = block.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from tach_lenh import shell_of, unreadable, variants  # shared reading and fail mode (0.8.0)
except Exception:  # helper missing: raw command only; GIT_GUARD_STRICT still honoured
    import os as _os

    def variants(cmd: str, shell: str | None = None) -> list[str]:
        return [cmd]

    def shell_of(data: object) -> str | None:
        return None

    def unreadable(reason: str, default: int = 0) -> int:
        strict = _os.environ.get("GIT_GUARD_STRICT", "").strip().lower() in ("1", "true", "yes", "on")
        return 2 if strict else default

CAY_CHINH = {"d:/aurelysn", "d:/aurelysn/05_evasion", "d:/aurelysn/04_portfolio"}

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", re.S)
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')


def norm_path(p: str) -> str:
    s = p.strip().strip('"').strip("'").replace("\\", "/")
    m = re.match(r"^/([a-zA-Z])/(.*)$", s)
    if m:
        s = f"{m.group(1)}:/{m.group(2)}"
    return s.rstrip("/").lower()


def is_cay_chinh(p: str) -> bool:
    return norm_path(p) in CAY_CHINH


SPLIT_SEG = re.compile(r"(?:;|&&|\|\||&|\n)+")
CD_CMD = re.compile(r"^\s*(?:cd|pushd|Set-Location|sl)\s+(?:/d\s+)?(\"[^\"]+\"|'[^']+'|\S+)", re.I)
GIT_C = re.compile(r"\bgit\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)")

# Branch-switching commands:
# 1. `gh pr checkout`
GH_PR_CO = re.compile(r"\bgh\s+pr\s+checkout\b")
# 2. `git switch` (always switches branches)
GIT_SWITCH = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)*switch\b")
# 3. `git checkout` WITHOUT `--` path separator
GIT_CHECKOUT = re.compile(r"\bgit\s+(?:-C\s+(?:\"[^\"]+\"|'[^']+'|\S+)\s+)*checkout\b([^\n;|&]*)")


def checkout_is_file_restore(tail: str) -> bool:
    """`git checkout -- file` or `git checkout HEAD -- file` restores files without switching branches."""
    tokens = tail.strip().split()
    if "--" in tokens:
        idx = tokens.index("--")
        before = tokens[:idx]
        # Reject branch creation flags before `--`
        if any(t in ("-b", "-B", "--orphan", "-t", "--track") for t in before):
            return False
        return True
    if any(t in ("-h", "--help", "-p", "--patch") for t in tokens):
        return True
    return False


def check(cmd: str, cwd: str) -> str | None:
    stripped = HEREDOC.sub("", cmd)
    cur_dir = cwd

    for seg in SPLIT_SEG.split(stripped):
        seg_clean = QUOTED.sub('""', seg)
        m_cd = CD_CMD.match(seg.strip())
        if m_cd:
            cur_dir = m_cd.group(1)
            continue

        target_dir = cur_dir
        m_c = GIT_C.search(seg)
        if m_c:
            target_dir = m_c.group(1)

        if not is_cay_chinh(target_dir):
            continue

        blocked = False
        if GH_PR_CO.search(seg_clean) or GIT_SWITCH.search(seg_clean):
            blocked = True
        else:
            # seg_clean, not seg: a quoted string that only MENTIONS `git checkout <x>` (a commit
            # message) is not a command. This case failed its own test until 2026-11-14.
            for m_co in GIT_CHECKOUT.finditer(seg_clean):
                if not checkout_is_file_restore(m_co.group(1)):
                    blocked = True
                    break

        if blocked:
            return (
                "CHẶN: không đổi nhánh (`git checkout <nhánh>` / `git switch` / `gh pr checkout`)\n"
                "  ngay trên cây chính của vault (`D:\\AureLysn`).\n"
                "  Cây chính phải đứng ở `main` vì Obsidian và các phiên khác đang đọc trực tiếp.\n"
                "  Cách đúng:\n"
                "    - Làm nhánh riêng: dùng `git worktree add ../AureLysn-wt/<tên> -b <nhánh>`.\n"
                "    - Khôi phục 1 file trên cây chính: dùng `git checkout -- <đường-dẫn-file>` (có `--`)."
            )
    return None


def main() -> int:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace"))
    except Exception:
        return unreadable("stdin không phải JSON")
    ti = (data.get("tool_input") or data.get("toolInput")) if isinstance(data, dict) else None
    if not isinstance(ti, dict):
        return unreadable("không có tool_input")
    cmd = ti.get("command") or ti.get("CommandLine") or ""
    if not isinstance(cmd, str):
        return unreadable("command không phải chuỗi")
    cwd = data.get("cwd") or data.get("currentWorkingDirectory") or os.getcwd()
    try:
        msg = None
        for v in variants(cmd, shell_of(data)):
            msg = check(v, cwd)
            if msg:
                break
    except Exception as e:
        return unreadable(f"lỗi khi kiểm: {type(e).__name__}: {e}", default=1)
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
