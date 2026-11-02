"""The excalidraw kit: its guard, its engine, and an agent that draws with it.

Three layers, as everywhere here. The `scripts` tests check what the wrapper
refuses, without installing anything. The `agent` layer installs the pinned
engine for real and drives it the way the skill tells an agent to, and then
hands the skill to an agent and checks the file it leaves behind.

What is asserted about a drawing is its structure - the labels exist and sit
inside their shapes - never its looks. Looks are the model's judgement, and a
test that scored them would be measuring the model.
"""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
from pathlib import Path

import pytest
from disposable_agent import DisposableAgent

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "skills" / "excalidraw" / "scripts" / "excalidraw.py"

_spec = importlib.util.spec_from_file_location("excalidraw_kit", SCRIPT)
assert _spec is not None and _spec.loader is not None
excalidraw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(excalidraw)


def labels(scene: dict) -> dict[str, str]:
    """Each bound label's text, keyed by the shape it sits in."""
    return {
        element["containerId"]: element["text"]
        for element in scene["elements"]
        if element.get("type") == "text" and element.get("containerId") and not element.get("isDeleted")
    }


# ---- the guard ---------------------------------------------------------------


@pytest.mark.scripts
@pytest.mark.parametrize(
    "args",
    [
        ["share"],
        ["install-skill", "--dir", "somewhere"],
        ["describe", "--url", "http://example.com"],
        ["describe", "--url=http://example.com"],
        ["export", "--out", "note.excalidraw.md"],
        ["export", "--out=NOTE.EXCALIDRAW.MD"],
        ["export", "--format", "obsidian", "--out", "a.excalidraw"],
        ["export", "--format=obsidian"],
    ],
)
def test_the_wrapper_refuses_what_an_agent_must_not_do_unasked(args: list[str]) -> None:
    with pytest.raises(excalidraw.RefusedError):
        excalidraw.check_arguments(args)


@pytest.mark.scripts
@pytest.mark.parametrize(
    "args",
    [
        [],
        ["help"],
        ["add"],
        ["export", "--out", "docs/page_diagram.excalidraw"],
        ["render", "page.excalidraw", "--out", "check.png"],
        ["update", "a", "--set", '{"text": "export --out x.md"}'],
    ],
)
def test_the_wrapper_passes_ordinary_commands(args: list[str]) -> None:
    excalidraw.check_arguments(args)


@pytest.mark.scripts
def test_a_refusal_exits_before_anything_is_installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert excalidraw.main(["share"]) == 2
    assert not any(tmp_path.iterdir())


@pytest.mark.scripts
def test_the_canvas_is_pinned_to_loopback_whatever_the_environment_says() -> None:
    hostile = {"EXPRESS_SERVER_URL": "http://example.com:80", "HOST": "0.0.0.0", "PORT": "80"}
    environ = excalidraw.engine_environment(hostile)
    assert environ["EXPRESS_SERVER_URL"] == "http://127.0.0.1:3000"
    assert environ["HOST"] == "127.0.0.1"
    assert environ["PORT"] == "3000"


@pytest.mark.scripts
def test_the_port_is_chosen_with_excalidraw_port() -> None:
    environ = excalidraw.engine_environment({"EXCALIDRAW_PORT": "4123"})
    assert environ["EXPRESS_SERVER_URL"] == "http://127.0.0.1:4123"
    assert environ["PORT"] == "4123"


@pytest.mark.scripts
@pytest.mark.parametrize("value", ["http", "0", "70000", "-1"])
def test_a_port_that_is_not_one_is_refused(value: str) -> None:
    with pytest.raises(excalidraw.RefusedError):
        excalidraw.engine_environment({"EXCALIDRAW_PORT": value})


@pytest.mark.scripts
def test_a_changed_lock_file_installs_a_fresh_engine(tmp_path: Path) -> None:
    """The cache is keyed on the lock, so a Dependabot bump is never served a stale engine."""
    (tmp_path / "package-lock.json").write_text('{"lockfileVersion": 3}', encoding="utf-8")
    before = excalidraw.engine_key(tmp_path)
    (tmp_path / "package-lock.json").write_text('{"lockfileVersion": 3, "x": 1}', encoding="utf-8")
    assert excalidraw.engine_key(tmp_path) != before


@pytest.mark.scripts
def test_the_engine_is_pinned_exactly() -> None:
    """A range in package.json would let `npm ci` refuse the lock on the next release."""
    manifest = json.loads((SCRIPT.parent / "engine" / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((SCRIPT.parent / "engine" / "package-lock.json").read_text(encoding="utf-8"))
    pinned = manifest["dependencies"][excalidraw.ENGINE_PACKAGE]
    assert pinned[0].isdigit(), f"{excalidraw.ENGINE_PACKAGE} is pinned to a range: {pinned}"
    assert lock["packages"][f"node_modules/{excalidraw.ENGINE_PACKAGE}"]["version"] == pinned


# ---- the engine, driven as the skill says ------------------------------------


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def engine(tmp_path: Path):
    """Run the script as an agent would, with its cache and state kept in `tmp_path`."""
    environ = {
        **os.environ,
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
        "LOCALAPPDATA": str(tmp_path / "local"),
        "EXCALIDRAW_PORT": str(free_port()),
    }
    work = tmp_path / "work"
    work.mkdir()

    def run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--script", str(SCRIPT), *args],
            input=stdin,
            cwd=work,
            env=environ,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
            check=False,
        )

    run.work = work  # type: ignore[attr-defined]
    yield run
    run("stop")


TWO_BOXES = json.dumps(
    [
        {"id": "bundle", "type": "rectangle", "x": 0, "y": 0, "width": 180, "height": 60, "text": "Bundle"},
        {"id": "diagram", "type": "rectangle", "x": 300, "y": 0, "width": 180, "height": 60, "text": "Diagram"},
        {"type": "arrow", "x": 0, "y": 0, "startElementId": "bundle", "endElementId": "diagram"},
    ]
)


@pytest.mark.agent
def test_the_engine_draws_exports_and_renders_a_diagram(engine) -> None:
    """The workflow in SKILL.md, step by step, against the pinned engine."""
    for step in (("clear", "--yes"), ("add",)):
        result = engine(*step, stdin=TWO_BOXES if step == ("add",) else None)
        assert result.returncode == 0, f"{step}: {result.stderr}"

    described = engine("describe")
    assert described.returncode == 0, described.stderr
    assert "Bundle" in described.stdout and "Diagram" in described.stdout

    shot = engine("screenshot")
    assert shot.returncode == 0, shot.stderr
    assert Path(json.loads(shot.stdout)["file"]).is_file()

    exported = engine("export", "--out", "page_diagram.excalidraw")
    assert exported.returncode == 0, exported.stderr
    target = engine.work / "page_diagram.excalidraw"
    scene = json.loads(target.read_text(encoding="utf-8"))
    assert scene["type"] == "excalidraw"
    assert sorted(labels(scene).values()) == ["Bundle", "Diagram"]

    assert engine("stop").returncode == 0
    rendered = engine("render", "page_diagram.excalidraw", "--out", "check.png")
    assert rendered.returncode == 0, rendered.stderr
    assert (engine.work / "check.png").stat().st_size > 0


@pytest.mark.agent
def test_the_engine_refuses_to_share(engine) -> None:
    result = engine("share")
    assert result.returncode == 2
    assert "refused" in result.stderr


# ---- an agent, given the skill -----------------------------------------------


@pytest.mark.agent
def test_an_agent_draws_a_diagram_into_a_file(kit_agent: DisposableAgent) -> None:
    """Asked for a sketch, an agent with the skill leaves a real `.excalidraw` file behind."""
    try:
        result = kit_agent.run(
            "Draw a small Excalidraw diagram with three boxes labelled Plan, Draw and Check, "
            "connected by arrows in that order, and save it as process.excalidraw in the "
            "current directory. Reply with the file name only."
        )
    finally:
        subprocess.run(
            [
                "uv",
                "run",
                "--script",
                str(kit_agent.agents_skills / "excalidraw" / "scripts" / "excalidraw.py"),
                "stop",
            ],
            env=kit_agent.env,
            cwd=kit_agent.work,
            capture_output=True,
            timeout=300,
            check=False,
        )

    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"
    drawn = kit_agent.work / "process.excalidraw"
    assert drawn.is_file(), f"no process.excalidraw was written\n--- transcript ---\n{result.text.strip()}"

    scene = json.loads(drawn.read_text(encoding="utf-8"))
    assert scene["type"] == "excalidraw"
    found = {
        element["text"].strip().lower()
        for element in scene["elements"]
        if element.get("type") == "text" and not element.get("isDeleted")
    }
    assert {"plan", "draw", "check"} <= found, f"labels in the file: {sorted(found)}"
    assert any(e.get("type") == "arrow" and not e.get("isDeleted") for e in scene["elements"])
    assert not list(kit_agent.work.glob("*.excalidraw.md")), "the Obsidian format was written"
