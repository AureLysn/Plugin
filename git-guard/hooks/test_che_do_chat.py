#!/usr/bin/env python3
"""Tests for the fail mode of the six git-guard hooks (plugin-benchmark-20261124 G4).

Default: input a hook cannot read is allowed (exit 0). With GIT_GUARD_STRICT=1 it is blocked
(exit 2), while readable commands are judged exactly as before. The `-I` runs hide
`tach_lenh.py` from the hook (isolated mode does not put the script's folder on sys.path),
so they test the fallback each hook carries for a missing helper.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).parent


def payload(cmd: str, cwd: str = "D:\\AureLysn") -> str:
    return json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": cwd,
                       "tool_input": {"command": cmd}})


NOT_JSON = "{khong phai json"
NO_INPUT = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash"})
READABLE = payload("git status")

def antigravity(cmd: str) -> str:
    return json.dumps({"toolName": "run_command", "cwd": "D:\\AureLysn", "toolInput": {"CommandLine": cmd}})


# One payload each hook blocks: a hard block, or an ask replayed with non-Claude keys.
BLOCKED = {
    "chan_git_mv.py": payload("git mv a.md b.md"),
    "chan_sed_i.py": payload("sed -i 's/a/b/' file.md"),
    "chan_nhap_temp.py": payload("python /tmp/fix.py"),
    "chan_exit_sau_ong.py": payload("python vault_doctor.py | tail -5; echo $?"),
    "chan_checkout_cay_chinh.py": payload("git checkout main"),
    "chan_git_pha_huy.py": payload("git add -A"),
    "chan_xoa_vinh_vien.py": antigravity("rm -rf D:/AureLysn/x"),
    "chan_sua_rao_chan.py": antigravity("echo x > CLAUDE.md"),
}
# These two judge paths with duong_dan.py; without the helpers they fall back to the fail mode.
PATH_HOOKS = {"chan_xoa_vinh_vien.py", "chan_sua_rao_chan.py"}

# (stdin, strict, isolated, expected exit, description); the stdin None means BLOCKED[hook].
CASES = [
    (NOT_JSON, False, False, 0, "JSON hỏng, mặc định: cho qua"),
    (NOT_JSON, True, False, 2, "JSON hỏng, GIT_GUARD_STRICT=1: chặn"),
    (NO_INPUT, False, False, 0, "thiếu tool_input, mặc định: cho qua"),
    (NO_INPUT, True, False, 2, "thiếu tool_input, chế độ chặt: chặn"),
    (READABLE, True, False, 0, "lệnh đọc được vẫn qua khi bật chế độ chặt"),
    (None, True, False, 2, "lệnh bị cấm vẫn bị chặn khi bật chế độ chặt"),
    (None, False, True, 2, "thiếu tach_lenh: hook vẫn chặn lệnh gõ thẳng"),
    (NOT_JSON, True, True, 2, "thiếu tach_lenh: chế độ chặt vẫn chặn JSON hỏng"),
    (READABLE, False, True, 0, "thiếu tach_lenh: lệnh thường vẫn qua"),
]


def run(hook: str, stdin: str, strict: bool, isolated: bool) -> int:
    env = dict(os.environ)
    env.pop("GIT_GUARD_STRICT", None)
    if strict:
        env["GIT_GUARD_STRICT"] = "1"
    args = [sys.executable] + (["-I"] if isolated else []) + [str(HERE / hook)]
    r = subprocess.run(args, input=stdin, capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode


def main() -> int:
    failed = total = 0
    for hook in BLOCKED:
        for stdin, strict, isolated, want, desc in CASES:
            if hook in PATH_HOOKS and stdin is None and isolated and not strict:
                want, desc = 0, "thiếu module: hook đường dẫn cho qua (mặc định mở)"
            got = run(hook, BLOCKED[hook] if stdin is None else stdin, strict, isolated)
            ok = got == want
            total += 1
            failed += not ok
            print(f"  [{'OK  ' if ok else 'FAIL'}] ({got}=={want}) {hook}: {desc}")
    print(f"\n{total - failed}/{total} ca đúng.")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
