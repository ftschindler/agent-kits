"""The excalidraw kit: its guard, its engine, and an agent that draws with it.

The `scripts` tests check what the wrapper accepts and refuses, without
installing anything. The `engine` tests install the pinned engine for real, which
needs the network, and drive it the way the skill tells an agent to. Whether an
agent follows the skill is the probe in tests/probes/excalidraw.json, recorded
on a contributor's machine.

What is asserted about a drawing is its structure - the labels exist and sit
inside their shapes - never its looks. Looks are the model's judgement, and a
test that scored them would be measuring the model.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

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
        ["d.excalidraw", "share"],
        ["d.excalidraw", "install-skill"],
        ["d.excalidraw", "export", "--out", "x.excalidraw"],
        ["d.excalidraw", "import", "other.excalidraw"],
        ["d.excalidraw", "clear", "--yes"],
        ["d.excalidraw", "mermaid"],
        ["d.excalidraw", "start"],
        ["note.excalidraw.md", "add"],
        ["diagram.json", "describe"],
        ["d.excalidraw", "describe", "--url", "http://example.com"],
        ["d.excalidraw", "describe", "--url=http://example.com"],
        ["render"],
        ["render", "note.excalidraw.md"],
        ["d.excalidraw"],
    ],
)
def test_the_wrapper_refuses_anything_outside_its_contract(args: list[str]) -> None:
    with pytest.raises(excalidraw.RefusedError):
        excalidraw.parse(args)


@pytest.mark.scripts
@pytest.mark.parametrize(
    ("args", "mode", "command"),
    [
        ([], "help", None),
        (["help", "add"], "help", None),
        (["d.excalidraw", "add"], "scene", "add"),
        (["D.EXCALIDRAW", "describe"], "scene", "describe"),
        (["sub/d.excalidraw", "update", "a", "--set", '{"text": "share x.md"}'], "scene", "update"),
        (["d.excalidraw", "screenshot", "--out", "check.png"], "scene", "screenshot"),
        (["render", "d.excalidraw", "--out", "check.png"], "render", None),
    ],
)
def test_the_wrapper_accepts_its_contract(args: list[str], mode: str, command: str | None) -> None:
    parsed_mode, _, rest = excalidraw.parse(args)
    assert parsed_mode == mode
    if command is not None:
        assert rest[0] == command


@pytest.mark.scripts
def test_a_refusal_exits_before_anything_is_installed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert excalidraw.main(["d.excalidraw", "share"]) == 2
    assert not any(tmp_path.iterdir())


@pytest.mark.scripts
def test_the_canvas_is_private_and_on_loopback_whatever_the_environment_says(tmp_path: Path) -> None:
    hostile = {"EXPRESS_SERVER_URL": "http://example.com:80", "HOST": "0.0.0.0", "PORT": "80"}
    environ = excalidraw.engine_environment(hostile, 4123, tmp_path)
    assert environ["EXPRESS_SERVER_URL"] == "http://127.0.0.1:4123"
    assert environ["HOST"] == "127.0.0.1"
    assert environ["PORT"] == "4123"
    assert environ["EXCALIDRAW_EXPORT_DIR"] == str(tmp_path)


@pytest.mark.scripts
def test_a_screenshot_is_made_in_the_sandbox_and_copied_where_asked(tmp_path: Path) -> None:
    wanted = tmp_path / "check.png"
    for args in (["screenshot", "--out", str(wanted)], ["screenshot", f"--out={wanted}"]):
        rewritten, image = excalidraw.redirect_image(args)
        assert str(wanted) not in " ".join(rewritten)
        assert image == ("image.png", wanted.resolve())
    assert excalidraw.redirect_image(["screenshot"]) == (["screenshot"], None)
    assert excalidraw.redirect_image(["add"]) == (["add"], None)


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


@pytest.fixture(scope="module")
def engine_cache(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """One engine install for the whole module, made before any test needs it.

    Installing once is faster, and it keeps the concurrency test about what it
    claims to test - two canvases staying apart - rather than two cold `npm ci`
    runs racing for one cache, which hung a Windows runner.
    """
    root = tmp_path_factory.mktemp("engine")
    environ = {
        **os.environ,
        "XDG_CACHE_HOME": str(root / "cache"),
        "XDG_STATE_HOME": str(root / "state"),
        "LOCALAPPDATA": str(root / "local"),
    }
    warmed = subprocess.run(
        ["uv", "run", "--script", str(SCRIPT), "help", "add"],
        env=environ,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert warmed.returncode == 0, warmed.stderr
    return environ


@pytest.fixture
def engine(tmp_path: Path, engine_cache: dict[str, str]):
    """Run the script as an agent would, from a fresh working directory, on the shared engine."""
    environ = engine_cache
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
    return run


def boxes(*names: str) -> str:
    shapes = [
        {"id": name.lower(), "type": "rectangle", "x": 300 * i, "y": 0, "width": 180, "height": 60, "text": name}
        for i, name in enumerate(names)
    ]
    arrows = [
        {"type": "arrow", "x": 0, "y": 0, "startElementId": a["id"], "endElementId": b["id"]}
        for a, b in itertools.pairwise(shapes)
    ]
    return json.dumps(shapes + arrows)


@pytest.mark.engine
def test_the_file_is_the_drawing_from_one_call_to_the_next(engine) -> None:
    """The workflow in SKILL.md, call by call, against the pinned engine."""
    added = engine("page_diagram.excalidraw", "add", stdin=boxes("Bundle", "Diagram"))
    assert added.returncode == 0, added.stderr
    target = engine.work / "page_diagram.excalidraw"
    assert sorted(labels(json.loads(target.read_text(encoding="utf-8"))).values()) == ["Bundle", "Diagram"]

    described = engine("page_diagram.excalidraw", "describe")
    assert described.returncode == 0, described.stderr
    assert "Bundle" in described.stdout and "Diagram" in described.stdout

    updated = engine("page_diagram.excalidraw", "update", "bundle", "--set", '{"width": 260}')
    assert updated.returncode == 0, updated.stderr
    scene = json.loads(target.read_text(encoding="utf-8"))
    assert next(e for e in scene["elements"] if e["id"] == "bundle")["width"] == 260

    shot = engine("page_diagram.excalidraw", "screenshot", "--out", "check.png")
    assert shot.returncode == 0, shot.stderr
    assert (engine.work / "check.png").stat().st_size > 0

    rendered = engine("render", "page_diagram.excalidraw", "--out", "offline.png")
    assert rendered.returncode == 0, rendered.stderr
    assert (engine.work / "offline.png").stat().st_size > 0

    assert sorted(p.name for p in engine.work.iterdir()) == ["check.png", "offline.png", "page_diagram.excalidraw"]


@pytest.mark.engine
def test_a_failed_command_leaves_the_file_untouched(engine) -> None:
    assert engine("kept.excalidraw", "add", stdin=boxes("Kept")).returncode == 0
    before = (engine.work / "kept.excalidraw").read_bytes()
    assert engine("kept.excalidraw", "update", "no-such-id", "--set", '{"width": 1}').returncode != 0
    assert (engine.work / "kept.excalidraw").read_bytes() == before


@pytest.mark.engine
def test_two_files_drawn_at_once_stay_apart(engine) -> None:
    """Every call has its own canvas, so concurrent sessions cannot mix their drawings."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda name: engine(f"{name.lower()}.excalidraw", "add", stdin=boxes(name)),
                ["Left", "Right"],
            )
        )
    assert all(result.returncode == 0 for result in results), [r.stderr for r in results]
    for name in ("Left", "Right"):
        scene = json.loads((engine.work / f"{name.lower()}.excalidraw").read_text(encoding="utf-8"))
        assert list(labels(scene).values()) == [name]


@pytest.mark.engine
def test_the_engine_refuses_to_share(engine) -> None:
    result = engine("page.excalidraw", "share")
    assert result.returncode == 2
    assert "refused" in result.stderr
