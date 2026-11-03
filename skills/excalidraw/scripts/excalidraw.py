#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["nodejs-wheel-binaries==24.19.0"]
# ///
"""excalidraw - draw into a `.excalidraw` file, with nothing but uv.

Usage:
  excalidraw.py <file.excalidraw> <command> [args...]
  excalidraw.py render <file.excalidraw> [--out image.png] [flags...]
  excalidraw.py help [command]

The file is the drawing, and the only state there is. Each call starts a
private canvas on a free loopback port, loads the file into it (or starts empty
when the file does not exist yet), runs the one command, writes the scene back
to the file when the command changed it, and stops the canvas. Nothing outlives
the call, so two sessions working on different files cannot see each other.

The drawing engine is `mcp-excalidraw-server`, at the version pinned in
`engine/package-lock.json`. Node comes from the `nodejs-wheel-binaries` wheel
declared above. The first run installs the engine into a cache directory keyed
on the lock file; later runs reuse it.

Only the commands below are passed on. Everything else the engine offers is
either done here (starting, stopping, loading and saving the canvas) or not
something an agent should do unasked.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from nodejs_wheel import node, npm

ENGINE_DIR = Path(__file__).resolve().parent / "engine"
ENGINE_PACKAGE = "mcp-excalidraw-server"
SUFFIX = ".excalidraw"

# Commands that change the scene, so the file is written back after them.
CHANGING = frozenset({"add", "apply", "update", "delete", "arrange"})
# Commands that only read it.
READING = frozenset({"describe", "get", "query", "screenshot"})
SCENE_COMMANDS = CHANGING | READING

USAGE = f"""\
usage: excalidraw.py <file{SUFFIX}> <command> [args...]
       excalidraw.py render <file{SUFFIX}> [--out image.png] [flags...]
       excalidraw.py help [command]

Commands that change the file: {", ".join(sorted(CHANGING))}
Commands that read it:         {", ".join(sorted(READING))}
"""


class RefusedError(Exception):
    """A call this script will not make, with the reason to show."""


def scene_path(raw: str) -> Path:
    if not raw.lower().endswith(SUFFIX):
        raise RefusedError(f"`{raw}` is not a {SUFFIX} file; the drawing is saved as plain {SUFFIX} JSON.")
    return Path(raw).resolve()


def parse(args: list[str]) -> tuple[str, Path | None, list[str]]:
    """Split a call into (mode, file, engine arguments), refusing anything outside the contract.

    The mode is `help`, `render` or `scene`. For `scene` the engine arguments
    start with the command.
    """
    if not args or args[0] in ("help", "--help", "-h"):
        return "help", None, args[1:2]
    if any(arg == "--url" or arg.startswith("--url=") for arg in args):
        raise RefusedError("`--url` is not accepted; every canvas is private and on loopback.")
    if args[0] == "render":
        if len(args) < 2:  # noqa: PLR2004 - `render` and its file
            raise RefusedError(f"`render` needs the {SUFFIX} file to render.")
        return "render", scene_path(args[1]), args[2:]
    if len(args) < 2:  # noqa: PLR2004 - the file and a command
        raise RefusedError(f"name the {SUFFIX} file and then a command.\n\n{USAGE}")
    path, command = scene_path(args[0]), args[1]
    if command not in SCENE_COMMANDS:
        raise RefusedError(f"`{command}` is not a command here.\n\n{USAGE}")
    return "scene", path, args[1:]


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def engine_environment(environ: dict[str, str], port: int, sandbox: Path) -> dict[str, str]:
    """The caller's environment with the canvas pinned to a private loopback port.

    Set explicitly rather than defaulted, because the engine loads a `.env` from
    its working directory and that file must not be able to move the canvas.
    The engine reads and writes files only inside `sandbox`.
    """
    return {
        **environ,
        "EXPRESS_SERVER_URL": f"http://127.0.0.1:{port}",
        "HOST": "127.0.0.1",
        "PORT": str(port),
        "EXCALIDRAW_EXPORT_DIR": str(sandbox),
    }


def cache_root(environ: dict[str, str]) -> Path:
    if sys.platform == "win32":
        base = environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Caches")
    else:
        base = environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "agent-kits" / "excalidraw"


def engine_key(engine_dir: Path = ENGINE_DIR) -> str:
    """Name the installed engine after what it was installed from, so a bumped lock installs afresh."""
    digest = hashlib.sha256((engine_dir / "package-lock.json").read_bytes())
    return digest.hexdigest()[:16]


def engine_entry(installed: Path) -> Path:
    return installed / "node_modules" / ENGINE_PACKAGE / "dist" / "bin.js"


def ensure_engine(environ: dict[str, str]) -> Path:
    """Install the pinned engine once, and return its entry point.

    The install happens in a scratch directory beside the target and is moved
    into place only once complete, so an interrupted run or two agents starting
    at once never leave a half-installed engine that later runs would trust.
    """
    root = cache_root(environ)
    target = root / engine_key()
    if engine_entry(target).is_file():
        return engine_entry(target)

    root.mkdir(parents=True, exist_ok=True)
    print("excalidraw: installing the drawing engine (first run only, about a minute)...", file=sys.stderr)
    scratch = Path(tempfile.mkdtemp(prefix=".install-", dir=root))
    try:
        for name in ("package.json", "package-lock.json"):
            shutil.copy2(ENGINE_DIR / name, scratch / name)
        # `npm ci` installs exactly the lock file; `--ignore-scripts` keeps every
        # dependency's install hook from running, which the engine does not need.
        code = npm(
            ["ci", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error"],
            cwd=scratch,
            env=environ,
            stdout=sys.stderr,
        )
        if code != 0 or not engine_entry(scratch).is_file():
            raise SystemExit(f"excalidraw: installing the engine failed (npm exited {code}).")
        try:
            scratch.rename(target)
        except OSError:
            # Another run finished first. Theirs is as good as ours.
            if not engine_entry(target).is_file():
                raise
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return engine_entry(target)


def redirect_image(engine_args: list[str]) -> tuple[list[str], tuple[str, Path] | None]:
    """Point a screenshot's `--out` into the sandbox, and say where to copy it afterwards.

    The engine writes only inside the sandbox, which is deleted when the call
    ends, so an image the caller asked for is made there and then copied out.
    """
    if engine_args[0] != "screenshot":
        return engine_args, None
    args = list(engine_args)
    for index, arg in enumerate(args):
        if arg.startswith("--out="):
            wanted = Path(arg.split("=", 1)[1])
            args[index] = f"--out=image{wanted.suffix}"
            return args, (f"image{wanted.suffix}", wanted.resolve())
        if arg == "--out" and index + 1 < len(args):
            wanted = Path(args[index + 1])
            args[index + 1] = f"image{wanted.suffix}"
            return args, (f"image{wanted.suffix}", wanted.resolve())
    return args, None


def quietly(entry: Path, args: list[str], env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run an engine step whose output is bookkeeping, keeping it for an error message."""
    return node(
        [str(entry), *args],
        env=env,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        return_completed_process=True,
    )


def run_scene(entry: Path, path: Path, engine_args: list[str], environ: dict[str, str]) -> int:
    """Load `path` into a private canvas, run one command, save if it changed anything, stop."""
    if not path.parent.is_dir():
        print(f"excalidraw: {path.parent} does not exist.", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="excalidraw-") as tmp:
        sandbox = Path(tmp)
        env = engine_environment(environ, free_port(), sandbox)
        steps = [["start"]]
        if path.is_file():
            shutil.copy2(path, sandbox / f"loaded{SUFFIX}")
            steps.append(["import", f"loaded{SUFFIX}", "--replace"])
        engine_args, image = redirect_image(engine_args)
        try:
            for step in steps:
                done = quietly(entry, step, env, sandbox)
                if done.returncode != 0:
                    sys.stderr.write(done.stdout + done.stderr)
                    return done.returncode

            # The one step whose output is the caller's: stdin, stdout and stderr pass through.
            code = node([str(entry), *engine_args], env=env, cwd=sandbox)
            if code == 0 and image is not None:
                shutil.copyfile(sandbox / image[0], image[1])
                print(f"excalidraw: image saved to {image[1]}", file=sys.stderr)
            if code != 0 or engine_args[0] not in CHANGING:
                return code

            done = quietly(entry, ["export", "--out", f"saved{SUFFIX}"], env, sandbox)
            if done.returncode != 0:
                sys.stderr.write(done.stdout + done.stderr)
                return done.returncode
            # Replace rather than write in place, so a reader never sees half a file.
            staged = path.with_name(f".{path.name}.tmp")
            shutil.copyfile(sandbox / f"saved{SUFFIX}", staged)
            staged.replace(path)
            return 0
        finally:
            quietly(entry, ["stop"], env, sandbox)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        mode, path, rest = parse(args)
    except RefusedError as refusal:
        print(f"excalidraw: refused: {refusal}", file=sys.stderr)
        return 2

    if mode == "help" and not rest:
        print(USAGE, end="")
        return 0

    environ = dict(os.environ)
    entry = ensure_engine(environ)
    if mode == "help":
        return node([str(entry), "help", *rest], env=environ)
    if mode == "render":
        return node([str(entry), "render", str(path), *rest], env=environ)
    return run_scene(entry, path, rest, environ)


if __name__ == "__main__":
    raise SystemExit(main())
