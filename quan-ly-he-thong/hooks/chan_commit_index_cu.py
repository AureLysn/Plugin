#!/usr/bin/env python3
"""PreToolUse hook (Bash): block `git commit` when the index of the repository being committed is stale.

Why: If an agent edits a note (such as `session-handoff.md` or a rule note) AFTER running
`vault_index.py --build`, committing immediately leaves the index out of sync with the notes
on disk. This hook intercepts `git commit`, finds the Git repository the commit lands in, and
when that repository holds an index (see REPO_INDEX) and has a staged `.md` file or its index
file staged, runs `vault_index.py --check` and blocks only if THAT repository's index is stale.

Repositories (Aurel, 2026-11-23, HT-043):
  vault root   -> 01_Origine/05_Meta/Index/vault-index.json        (root 1)
  05_Evasion/  -> 05_Evasion/01_Oeuvre/System/runtime/index.json  (root 2, fiction)
  any other repository (04_Portfolio/, app repositories) has no index and is skipped.

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
CD_CMD = re.compile(r"^\s*(?:cd|pushd|Push-Location|Set-Location|sl)\s+(?:-Path\s+|-LiteralPath\s+)?(?:/d\s+)?(\"[^\"]+\"|'[^']+'|\S+)", re.I)
GIT_C = re.compile(r"\bgit\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)")
GIT_COMMIT = re.compile(r"\bgit\b(?:\s+-C\s+\S+)*\s+commit\b")
COMMIT_HELP = re.compile(r"\s(?:-h|--help)\b")
COMMIT_ALL = re.compile(r"\s(?:-[a-zA-Z]*a[a-zA-Z]*|--all)\b")
# Repository path relative to the vault root ("" = the vault root repository) -> its index,
# relative to the vault root (this is also how `vault_index.py --check` names it).
REPO_INDEX = {
    "": "01_Origine/05_Meta/Index/vault-index.json",
    "05_Evasion": "05_Evasion/01_Oeuvre/System/runtime/index.json",
}

INDEX_SCRIPT_CANDIDATES = (
    Path("01_Origine/04_Tools/VaultTool/Core/vault_index.py"),
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
        if (c / "CLAUDE.md").is_file():
            for rel in INDEX_SCRIPT_CANDIDATES:
                if (c / rel).is_file():
                    return c, c / rel
    return None


def repo_top(start: Path) -> Path | None:
    """Top folder of the Git repository that contains `start` (None if not a repository)."""
    if not start.is_dir():
        return None
    r = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0 or not r.stdout.strip():
        return None
    return norm_win(r.stdout.strip())


def staged_files(repo: Path) -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-only"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        return []
    return [ln.strip().replace("\\", "/") for ln in r.stdout.splitlines() if ln.strip()]


def modified_tracked(repo: Path) -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        return []
    return [ln.strip().replace("\\", "/") for ln in r.stdout.splitlines() if ln.strip()]


def repo_key(vault: Path, repo: Path) -> str | None:
    """Path of `repo` relative to `vault` in posix form ("" for the vault root)."""
    try:
        rel = repo.resolve().relative_to(vault.resolve())
    except (OSError, ValueError):
        return None
    key = rel.as_posix()
    return "" if key == "." else key


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

        repo = repo_top(target_dir)
        if repo is None:
            continue
        found = find_vault(repo)
        if not found:
            continue
        vault, idx_script = found
        key = repo_key(vault, repo)
        if key not in REPO_INDEX:
            continue  # repository without an index (04_Portfolio/, apps)
        index_vault_rel = REPO_INDEX[key]
        index_repo_rel = index_vault_rel[len(key) + 1:] if key else index_vault_rel

        files = modified_tracked(repo) if COMMIT_ALL.search(seg_clean) else staged_files(repo)
        has_md = any(f.lower().endswith(".md") for f in files)
        has_idx = index_repo_rel in files
        if not (has_md or has_idx):
            continue

        r = subprocess.run(
            [sys.executable, str(idx_script), "--check"],
            cwd=str(vault), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if r.returncode == 0:
            continue
        detail = (r.stdout + r.stderr).strip()
        # `--check` reports each stale index on a line that starts with its path;
        # block only when the stale one belongs to this repository.
        stale_here = any(ln.strip().startswith(index_vault_rel + ":") for ln in detail.splitlines())
        if not stale_here:
            continue
        rel_script = idx_script.relative_to(vault).as_posix()
        add_cmd = f"git -C {key} add {index_repo_rel}" if key else f"git add {index_repo_rel}"
        return (
            f"CHẶN: không `git commit` khi index của repo này ({index_vault_rel}) đang CŨ so với note trên đĩa.\n"
            f"{detail}\n"
            "  Cách sửa (chạy SAU CÙNG trước khi commit, từ gốc vault):\n"
            f"    python {rel_script} --build --include-fiction\n"
            f"    {add_cmd}"
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
