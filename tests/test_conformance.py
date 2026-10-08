"""The kits in this repository are shaped the way akit discovers one.

This layer reads what is committed and nothing else: no network, no agent, no
subprocess. It is the test that fails when a skill is renamed in one place and
not the other, which is a failure that otherwise only appears on somebody else's
machine as a part that silently does not exist.

The checker itself is unit-tested against crafted trees in test_scripts.py. Both
halves are needed: this one would keep passing if the checker stopped checking,
and that one would keep passing while the real kits rotted.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from kit_layout import REPO_ROOT, check_all, check_flat_kind, check_skills, frontmatter_block

pytestmark = pytest.mark.conformance

CHECK_KIT_LAYOUT = REPO_ROOT / ".scripts" / "check_kit_layout.py"


def test_every_skill_is_discoverable_and_installs_under_its_own_name():
    assert check_skills() == []


def test_every_rule_declares_what_it_is_for():
    assert check_flat_kind("rules") == []


def test_every_agent_declares_what_it_is_for():
    assert check_flat_kind("agents") == []


def test_the_whole_repository_passes_its_own_layout_check():
    assert check_all() == []


def test_the_checker_runs_as_a_command_and_reports_success():
    """The hook and CI run it as a script, so the script's exit code is the contract.

    Calling the functions directly, as the tests above do, would keep passing
    through a broken `main()` - a missing dependency, an argument parsed wrongly,
    a non-zero exit on a clean tree. That is what the hook actually invokes.
    """
    result = subprocess.run(
        [sys.executable, str(CHECK_KIT_LAYOUT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_no_kit_directory_holds_a_part_too_deep_to_find():
    """Three levels is as far as akit walks, and a part below it is invisible.

    Covered by the checks above too, which is deliberate: this states the rule
    by name so a failure says which one broke rather than only where.
    """
    for kind in ("skills", "rules", "agents"):
        directory = REPO_ROOT / kind
        if not directory.is_dir():
            continue
        for path in directory.rglob("*.md"):
            depth = len(path.relative_to(directory).parts)
            assert depth <= 3, f"{path.relative_to(REPO_ROOT)} sits {depth} levels deep"


def test_a_part_is_not_committed_where_a_render_would_land():
    """`.agents/` is output, so a source directory there would be read as input.

    akit subtracts its own render record from discovery, but a *committed*
    `.agents/` predates any record and would be discovered as a hand-written
    part - doubling every kit it holds on the next render.
    """
    rendered = subprocess.run(
        ["git", "ls-files", ".agents"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert rendered.stdout.strip() == "", "`.agents/` is rendered output and must not be committed"


def test_at_least_one_kit_is_shipped():
    """An empty repository passes every check above by having nothing to check.

    That is the state this repository was in for exactly one commit, and a suite
    that stays green through it tells a contributor nothing. Now that a kit is
    here, this is what notices if the directory holding it disappears.
    """
    kits = list((REPO_ROOT / "skills").glob("*/")) + list((REPO_ROOT / "rules").glob("*.md"))
    assert kits, "no skills and no rules: this repository ships nothing"


def test_a_rule_is_shorter_than_the_skill_it_digests():
    """A rule is paid for on every turn; a skill is read when it is needed.

    `writing` exists in both forms deliberately. The day the digest grows past
    the skill, the reason for having two has gone, and nothing else would say so.
    """
    rule = (REPO_ROOT / "rules" / "writing.md").read_text(encoding="utf-8")
    skill = (REPO_ROOT / "skills" / "writing" / "SKILL.md").read_text(encoding="utf-8")
    assert len(rule) < len(skill), "the digest is longer than the skill it digests"


def reference_files() -> list[Path]:
    return sorted(REPO_ROOT.glob("skills/*/references/*.md"))


def test_a_reference_carries_no_frontmatter():
    """A reference is a digest the skill ships, not a wiki concept it copied.

    The pages these are distilled from are Open Knowledge Format concepts, and
    their frontmatter carries `type`, `tags`, `status` and a `generated` stamp
    that would be false the moment the digest diverges. A reader of the skill
    has no use for any of it, and the model reading the file pays for it.
    """
    for path in reference_files():
        block, error = frontmatter_block(path)
        assert error is None, f"{path.relative_to(REPO_ROOT)}: {error}"
        assert block is None, f"{path.relative_to(REPO_ROOT)}: carries frontmatter the skill has no use for"


def test_every_reference_is_reachable_from_its_skill():
    """A reference nothing links to is one the model never opens.

    The whole reason these ship beside the skill rather than as URLs is that a
    link out to the web does not get followed. An unlinked file is the same
    failure one step earlier.
    """
    for path in reference_files():
        skill = path.parent.parent / "SKILL.md"
        linked = f"references/{path.name}" in skill.read_text(encoding="utf-8")
        assert linked, f"{path.relative_to(REPO_ROOT)} is not linked from {skill.relative_to(REPO_ROOT)}"


def test_every_reference_names_the_live_page_it_was_distilled_from():
    """The wiki is the authority, and a digest that cannot be traced back is a fork."""
    for path in reference_files():
        text = path.read_text(encoding="utf-8")
        assert "https://ftschindler.github.io/knowledge/" in text, (
            f"{path.relative_to(REPO_ROOT)} does not link the page it digests"
        )
