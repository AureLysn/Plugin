#!/usr/bin/env python3
"""Unit tests for chan_commit_index_cu.py (`0` = allow, `2` = block).

The fake vault mirrors the real layout: the vault root is one Git repository,
`05_Evasion/` and `04_Portfolio/` are separate repositories nested inside it.
The mock `vault_index.py --check` reports the indexes named in STALE.txt as stale.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOOK = Path(__file__).with_name("chan_commit_index_cu.py")
ROOT_IDX = "01_Origine/05_Meta/Index/vault-index.json"
FIC_IDX = "05_Evasion/01_Oeuvre/System/runtime/index.json"

MOCK_INDEX = '''import sys
from pathlib import Path
stale = [l for l in Path(__file__).with_name("STALE.txt").read_text(encoding="utf-8").splitlines() if l]
if not stale:
    print("Index khop voi note (goc 1 va goc 2).")
    sys.exit(0)
print("INDEX CU — dung lai roi moi commit:")
for s in stale:
    print("  " + s + ": 1 note lech")
sys.exit(2)
'''


def git_init(repo: Path, first_file: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(repo), check=True)
    subprocess.run(["git", "add", first_file], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(repo), check=True)


def make_fake_vault(tmp: Path, stale: list[str]) -> Path:
    vault = tmp / "vault"
    script_dir = vault / "01_Origine/04_Tools/VaultTool/Core"
    script_dir.mkdir(parents=True)
    (vault / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    (vault / ".gitignore").write_text("05_Evasion/\n04_Portfolio/\n", encoding="utf-8")
    (script_dir / "vault_index.py").write_text(MOCK_INDEX, encoding="utf-8")
    (script_dir / "STALE.txt").write_text("\n".join(stale) + "\n", encoding="utf-8")
    git_init(vault, "CLAUDE.md")
    for sub in ("05_Evasion", "04_Portfolio"):
        d = vault / sub
        d.mkdir()
        (d / "README.md").write_text("# repo\n", encoding="utf-8")
        git_init(d, "README.md")
    return vault


def stage(repo: Path, name: str) -> None:
    f = repo / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", name], cwd=str(repo), check=True)


def run_raw(stdin: str, strict: bool) -> int:
    env = dict(os.environ)
    env.pop("GIT_GUARD_STRICT", None)
    if strict:
        env["GIT_GUARD_STRICT"] = "1"
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin,
                       capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode


def run_hook(cmd: str, cwd: Path, tool: str = "Bash") -> int:
    payload = json.dumps({
        "tool_name": tool,
        "cwd": str(cwd),
        "tool_input": {"command": cmd},
    })
    r = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, encoding="utf-8")
    return r.returncode


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test_chan_idx_"))
    cases: list[tuple[str, int, int]] = []

    def case(label: str, got: int, want: int) -> None:
        cases.append((label, got, want))

    try:
        # 1. vault root: .md staged, root index stale -> block
        v = make_fake_vault(tmp / "c1", [ROOT_IDX])
        stage(v, "note.md")
        case("gốc vault: .md staged, index gốc 1 cũ -> chặn", run_hook('git commit -m "x"', v), 2)

        # 2. vault root: .md staged, all indexes fresh -> allow
        v = make_fake_vault(tmp / "c2", [])
        stage(v, "note.md")
        case("gốc vault: index khớp -> cho qua", run_hook('git commit -m "x"', v), 0)

        # 3. vault root: only .py staged -> allow even if stale
        v = make_fake_vault(tmp / "c3", [ROOT_IDX])
        stage(v, "tool.py")
        case("gốc vault: chỉ .py -> không kiểm", run_hook('git commit -m "x"', v), 0)

        # 4. folder outside any vault -> allow
        other = tmp / "other"
        other.mkdir()
        case("ngoài vault -> cho qua", run_hook('git commit -m "x"', other), 0)

        # 5. 05_Evasion via `git -C` from vault root: .md staged, fiction index stale -> block
        v = make_fake_vault(tmp / "c5", [FIC_IDX])
        stage(v / "05_Evasion", "01_Oeuvre/note.md")
        case("05_Evasion: .md staged, index gốc 2 cũ -> chặn",
             run_hook('git -C 05_Evasion commit -m "x"', v), 2)

        # 6. 05_Evasion: .md staged, only root index stale -> allow (not this repo's index)
        v = make_fake_vault(tmp / "c6", [ROOT_IDX])
        stage(v / "05_Evasion", "01_Oeuvre/note.md")
        case("05_Evasion: chỉ index gốc 1 cũ -> cho qua",
             run_hook('git -C 05_Evasion commit -m "x"', v), 0)

        # 7. vault root: .md staged, only fiction index stale -> allow
        v = make_fake_vault(tmp / "c7", [FIC_IDX])
        stage(v, "note.md")
        case("gốc vault: chỉ index gốc 2 cũ -> cho qua", run_hook('git commit -m "x"', v), 0)

        # 8. 04_Portfolio (no index): .md staged, both stale -> allow
        v = make_fake_vault(tmp / "c8", [ROOT_IDX, FIC_IDX])
        stage(v / "04_Portfolio", "page.md")
        case("04_Portfolio (không có index) -> bỏ qua",
             run_hook('git commit -m "x"', v / "04_Portfolio"), 0)

        # 9. 05_Evasion: only the fiction index staged, stale -> block
        v = make_fake_vault(tmp / "c9", [FIC_IDX])
        stage(v / "05_Evasion", "01_Oeuvre/System/runtime/index.json")
        case("05_Evasion: chỉ stage index, index cũ -> chặn",
             run_hook('git -C 05_Evasion commit -m "x"', v), 2)

        # 10. PowerShell tool with Push-Location into 05_Evasion -> block
        v = make_fake_vault(tmp / "c10", [FIC_IDX])
        stage(v / "05_Evasion", "01_Oeuvre/note.md")
        case("PowerShell: Push-Location 05_Evasion; git commit -> chặn",
             run_hook('Push-Location 05_Evasion; git commit -m "x"; Pop-Location', v, tool="PowerShell"), 2)

        # 11-15. commits handed to another program (plugin-benchmark-20261124 N5; allowed until 0.10.0)
        v = make_fake_vault(tmp / "c11", [ROOT_IDX])
        stage(v, "note.md")
        case("bọc trong bash -c, index cũ -> chặn", run_hook('bash -c "git commit -m x"', v), 2)
        case("bọc trong powershell -Command, index cũ -> chặn",
             run_hook('powershell -NoProfile -Command "git commit -m x"', v, tool="PowerShell"), 2)
        case("trong khối if của PowerShell, index cũ -> chặn",
             run_hook('if ($true) { git commit -m "x" }', v, tool="PowerShell"), 2)
        case("chỉ nhắc trong echo -> cho qua", run_hook('echo "bash -c \'git commit -m x\'"', v), 0)
        v = make_fake_vault(tmp / "c15", [])
        stage(v, "note.md")
        case("bọc trong bash -c, index khớp -> cho qua", run_hook('bash -c "git commit -m x"', v), 0)

        # 16-17. fail mode (G4)
        case("JSON hỏng, mặc định -> cho qua", run_raw("{khong phai json", False), 0)
        case("JSON hỏng, GIT_GUARD_STRICT=1 -> chặn", run_raw("{khong phai json", True), 2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failed = 0
    for label, got, want in cases:
        ok = got == want
        failed += not ok
        print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}=={want}) {label}")
    print(f"\n{len(cases) - failed}/{len(cases)} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
