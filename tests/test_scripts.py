"""Unit tests for the guards under .scripts/.

Fast and deterministic: no LLM, no network. Each test builds a crafted tree in a
temp directory and points the checker at it, so what is asserted is that the
guard *catches* things - a guard exercised only against a conformant repository
passes just as happily once it has stopped checking anything.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from git_environment import outside_any_repository
from kit_layout import REPO_ROOT, check_all, read_frontmatter

pytestmark = pytest.mark.scripts

CHECK_MARKDOWN_STYLE = REPO_ROOT / ".scripts" / "check_markdown_style.py"
CHECK_MAILMAP = REPO_ROOT / ".scripts" / "check_mailmap.py"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def skill(root: Path, directory: str, *, name: str | None = "x", description: str | None = "What it does.") -> Path:
    lines = ["---"]
    if name is not None:
        lines.append(f"name: {name}")
    if description is not None:
        lines.append(f"description: {description}")
    lines += ["---", "", "# A skill", ""]
    return write(root / "skills" / directory / "SKILL.md", "\n".join(lines))


def rule(root: Path, filename: str, body: str) -> Path:
    return write(root / "rules" / filename, body)


def test_a_conformant_tree_passes(tmp_path: Path):
    skill(tmp_path, "writing", name="writing")
    rule(tmp_path, "writing.md", "---\ndescription: House prose style.\n---\n\n# Writing\n")
    assert check_all(tmp_path) == []


def test_a_skill_whose_name_does_not_match_its_directory_is_caught(tmp_path: Path):
    skill(tmp_path, "writing", name="prose")
    problems = check_all(tmp_path)
    assert len(problems) == 1
    assert "does not match its directory" in problems[0]


def test_a_skill_with_no_description_is_caught(tmp_path: Path):
    skill(tmp_path, "writing", name="writing", description=None)
    assert any("description" in problem for problem in check_all(tmp_path))


def test_a_skill_with_an_empty_description_is_caught(tmp_path: Path):
    skill(tmp_path, "writing", name="writing", description='""')
    assert any("description" in problem for problem in check_all(tmp_path))


def test_a_skill_with_no_frontmatter_at_all_is_caught(tmp_path: Path):
    write(tmp_path / "skills" / "writing" / "SKILL.md", "# A skill with nothing declared\n")
    assert len(check_all(tmp_path)) == 2


def test_unclosed_frontmatter_is_reported_rather_than_ignored(tmp_path: Path):
    write(tmp_path / "skills" / "writing" / "SKILL.md", "---\nname: writing\n\n# Oops\n")
    assert any("never closed" in problem for problem in check_all(tmp_path))


def test_a_directory_under_skills_holding_no_skill_is_caught(tmp_path: Path):
    (tmp_path / "skills" / "halfway").mkdir(parents=True)
    write(tmp_path / "skills" / "halfway" / "references.md", "# Notes\n")
    assert any("nothing here is installable" in problem for problem in check_all(tmp_path))


def test_a_loose_file_directly_under_skills_is_caught(tmp_path: Path):
    skill(tmp_path, "writing", name="writing")
    write(tmp_path / "skills" / "README.md", "# Not a skill\n")
    assert any("no loose files" in problem for problem in check_all(tmp_path))


def test_a_skill_in_a_category_directory_is_accepted(tmp_path: Path):
    """Three levels is allowed, so categorising later needs no migration."""
    skill(tmp_path, "prose/writing", name="writing")
    assert check_all(tmp_path) == []


def test_a_skill_buried_too_deep_to_be_discovered_is_caught(tmp_path: Path):
    skill(tmp_path, "a/b/c/writing", name="writing")
    assert any("deeper than" in problem for problem in check_all(tmp_path))


def test_a_rule_with_no_description_is_caught(tmp_path: Path):
    rule(tmp_path, "writing.md", "# Writing\n\nNo frontmatter, so Copilot never loads it.\n")
    assert any("description" in problem for problem in check_all(tmp_path))


def test_a_rule_whose_name_contradicts_its_filename_is_caught(tmp_path: Path):
    rule(tmp_path, "writing.md", "---\nname: prose\ndescription: House style.\n---\n\n# Writing\n")
    assert any("does not match the filename" in problem for problem in check_all(tmp_path))


def test_a_rule_that_is_not_markdown_is_caught(tmp_path: Path):
    write(tmp_path / "rules" / "writing.txt", "House style.\n")
    assert any("is not one" in problem for problem in check_all(tmp_path))


def test_an_absent_kind_directory_is_not_a_failure(tmp_path: Path):
    """`agents/` arrives when the first agent does, and not before."""
    skill(tmp_path, "writing", name="writing")
    assert check_all(tmp_path) == []


def test_frontmatter_survives_a_description_holding_a_colon(tmp_path: Path):
    path = write(
        tmp_path / "skills" / "writing" / "SKILL.md",
        '---\nname: writing\ndescription: "Use when: a draft reads as promotional."\n---\n\n# Writing\n',
    )
    frontmatter, error = read_frontmatter(path)
    assert error is None
    assert frontmatter["description"].startswith("Use when:")
    assert check_all(tmp_path) == []


def test_the_markdown_style_guard_rejects_an_em_dash(tmp_path: Path):
    offending = write(tmp_path / "doc.md", "A sentence \u2014 with an em dash.\n")
    result = subprocess.run(
        [sys.executable, str(CHECK_MARKDOWN_STYLE), str(offending)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_the_mailmap_guard_survives_a_repository_with_no_commits(tmp_path: Path):
    """The very first commit of a repository runs this hook, and `git log` exits 128 there.

    Found on this repository's own first commit, where the guard died in a
    traceback naming neither the file nor the problem.
    """
    repo = tmp_path / "fresh"
    repo.mkdir()
    write(repo / ".mailmap", "Ada Lovelace <ada@example.com>\n")
    subprocess.run(
        ["git", "init", "-q", "-b", "main"],
        cwd=repo,
        check=True,
        env=outside_any_repository(),
        capture_output=True,
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_MAILMAP)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=outside_any_repository(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
