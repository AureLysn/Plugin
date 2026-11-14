#!/usr/bin/env python3
"""PreToolUse hook (Bash): block `git commit` when the vault search index is stale.

Why: If an agent edits a note (such as `session-handoff.md` or a rule note) AFTER running
`vault_index.py --build`, committing immediately leaves `vault-index.json` out of sync with
the notes on disk. This hook intercepts `git commit` inside the vault and runs
`vault_index.py --check` whenever any indexed `.md` file is staged.

Exit 0 = allow, 2 = block (stderr shown to Claude).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", re.S)
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
SPLIT_SEG = re.compile(r"(?:;|&&|\|\||&|\n)+")
CD_CMD = re.compile(r"^\s*(?:cd|pushd|Set-Location|sl)\s+(?:/d\s+)?(\"[^\"]+\"|'[^']+'|\S+)", re.I)
GIT_C = re.compile(r"\bgit\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)")
GIT_COMMIT = re.compile(r"\bgit\b(?:\s+-C\s+\S+)*\s+commit\b")
COMMIT_HELP = re.compile(r"\s(?:-h|--help)\b")
COMMIT_ALL = re.compile(r"\s(?:-[a-zA-Z]*a[a-zA-Z]*|--all)\b")
INDEX_JSON = {
    "01_Origine/05_Meta/Index/vault-index.json",
    "90_Meta/index/vault-index.json",
    "05_Evasion/01_Oeuvre/System/runtime/index.json",
    "60_Personal/fiction/System/runtime/index.json",
}

INDEX_SCRIPT_CANDIDATES = (
    Path("01_Origine/04_Tools/VaultTool/Core/vault_index.py"),
    Path("70_Systems/vault-tools/vault_index.py"),
)


def norm_win(p: str) -> Path:
    s = p.strip().strip('"').strip("'")
    m = re.match(r"^/([a-zA-Z])/(.*)$", s)
    if m:
        s = f"{m.group(1)}:/{m.group(2)}"
    return Path(s)


def find_vault(start: Path) -> tuple[Path, Path] | None:
    try:
        cur = start.resolve()
    except OSError:
        cur = start
    for c in [cur, *cur.parents]:
        if (c / "AGENTS.md").is_file():
            for rel in INDEX_SCRIPT_CANDIDATES:
                if (c / rel).is_file():
                    return c, c / rel
    return None


def staged_files(vault: Path) -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(vault), "diff", "--cached", "--name-only"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        return []
    return [ln.strip().replace("\\", "/") for ln in r.stdout.splitlines() if ln.strip()]


def modified_tracked(vault: Path) -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(vault), "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        return []
    return [ln.strip().replace("\\", "/") for ln in r.stdout.splitlines() if ln.strip()]


def check_cmd(cmd: str, cwd: str) -> str | None:
    stripped = HEREDOC.sub("", cmd)
    cur_dir = norm_win(cwd)

    for seg in SPLIT_SEG.split(stripped):
        seg_clean = QUOTED.sub('""', seg)
        m_cd = CD_CMD.match(seg.strip())
        if m_cd:
            cand = norm_win(m_cd.group(1))
            cur_dir = cand if cand.is_absolute() else (cur_dir / cand)
            continue

        if not GIT_COMMIT.search(seg_clean):
            continue
        if COMMIT_HELP.search(seg_clean):
            continue

        target_dir = cur_dir
        m_c = GIT_C.search(seg)
        if m_c:
            cand = norm_win(m_c.group(1))
            target_dir = cand if cand.is_absolute() else (cur_dir / cand)

        found = find_vault(target_dir)
        if not found:
            continue
        vault, idx_script = found

        files = modified_tracked(vault) if COMMIT_ALL.search(seg_clean) else staged_files(vault)
        has_md = any(f.lower().endswith(".md") for f in files)
        has_idx = any(f in INDEX_JSON for f in files)
        if not (has_md or has_idx):
            continue

        r = subprocess.run(
            [sys.executable, str(idx_script), "--check"],
            cwd=str(vault), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if r.returncode != 0:
            detail = (r.stdout + r.stderr).strip()
            rel_script = idx_script.relative_to(vault).as_posix()
            return (
                "CHẶN: không `git commit` khi index của vault đang CŨ so với note trên đĩa.\n"
                f"{detail}\n"
                "  Cách sửa (chạy SAU CÙNG trước khi commit):\n"
                f"    python {rel_script} --build --include-fiction\n"
                "    git add 01_Origine/05_Meta/Index/vault-index.json"
            )
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    ti = data.get("tool_input") or data.get("toolInput") or {}
    cmd = ti.get("command") or ti.get("CommandLine") or ""
    cwd = data.get("cwd") or data.get("currentWorkingDirectory") or os.getcwd()
    msg = check_cmd(cmd, cwd)
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
