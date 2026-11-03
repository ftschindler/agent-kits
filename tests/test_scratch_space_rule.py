"""The scratch-space rule's commands do what the rule says they do.

A rule is followed by copying its commands, so a command that fails, or that
hands two calls the same directory, teaches every agent the wrong thing at once.
These tests run each command block exactly as written, twice, and check the
result: two distinct new directories, under the temporary directory, named for
the task.

Whether an agent follows the rule is not asserted here. That would measure the
model rather than the rule.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from kit_layout import REPO_ROOT

pytestmark = pytest.mark.scripts

RULE = REPO_ROOT / "rules" / "scratch-space.md"
# The placeholders the rule tells an agent to replace, and what the test puts there.
HARNESS_PARENT = "/tmp/<harness>"
TASK = "<task>"
PREFIX = "probe-task"


def command(language: str) -> str:
    """The rule's command block for `language`, with `<task>` filled in as an agent would."""
    blocks = re.findall(rf"```{language}\n(.*?)```", RULE.read_text(encoding="utf-8"), re.DOTALL)
    assert len(blocks) == 1, f"expected one ```{language} block in {RULE.name}, found {len(blocks)}"
    line = blocks[0].strip()
    assert TASK in line, f"the {language} example no longer names {TASK}; update this test"
    return line.replace(TASK, PREFIX)


def run_twice(argv: list[str], tmp_path: Path) -> list[Path]:
    env = {**os.environ, "TMPDIR": str(tmp_path), "TEMP": str(tmp_path), "TMP": str(tmp_path)}
    made = []
    for _ in range(2):
        result = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=60, check=False)
        assert result.returncode == 0, result.stderr
        made.append(Path(result.stdout.strip()))
    return made


def assert_fresh_and_distinct(made: list[Path], tmp_path: Path) -> None:
    first, second = made
    assert first != second, "two calls handed out the same directory"
    for path in made:
        assert path.is_dir(), f"{path} was printed but not created"
        assert path.resolve().parent == tmp_path.resolve(), f"{path} is not under the temporary directory"
        assert path.name.startswith(PREFIX), f"{path.name} does not start with the task's name"


@pytest.mark.skipif(sys.platform == "win32", reason="the POSIX command is for POSIX shells")
def test_the_posix_command_makes_a_fresh_directory_each_time(tmp_path: Path) -> None:
    line = command("sh")
    assert HARNESS_PARENT in line, f"the example no longer names {HARNESS_PARENT}; update this test"
    made = run_twice(["sh", "-c", line.replace(HARNESS_PARENT, str(tmp_path))], tmp_path)
    assert_fresh_and_distinct(made, tmp_path)


def test_the_powershell_command_makes_a_fresh_directory_each_time(tmp_path: Path) -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("no PowerShell on this machine")
    made = run_twice([shell, "-NoProfile", "-NonInteractive", "-Command", command("powershell")], tmp_path)
    assert_fresh_and_distinct(made, tmp_path)
