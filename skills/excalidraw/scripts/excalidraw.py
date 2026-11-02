#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["nodejs-wheel-binaries==24.19.0"]
# ///
"""excalidraw - draw Excalidraw diagrams from the command line, with nothing but uv.

Usage:
  excalidraw.py <command> [args...]
  excalidraw.py help [command]

Every command is passed to the drawing engine, `mcp-excalidraw-server`, at the
version pinned in `engine/package-lock.json`. Node comes from the
`nodejs-wheel-binaries` wheel declared above, so a machine needs `uv` and
nothing else. The first run installs the engine into a cache directory, keyed on
the lock file, and later runs reuse it.

The engine can do more than a skill should let an agent do unasked, so a few
things are refused here rather than left to the instructions:

- `share` uploads the scene to excalidraw.com, which is publishing.
- `install-skill` writes a second, competing skill into the agent's own setup.
- `--url`, and a `.env` in the working directory, could point the engine at a
  canvas on another host. The canvas URL is always set here, on loopback.
- an `export` to `.md` writes the Obsidian wrapper format, which most renderers
  outside Obsidian cannot read. Plain `.excalidraw` JSON is the portable form.
- no command at all starts the engine's MCP stdio server, which waits on stdin
  forever. Help is printed instead.

EXCALIDRAW_PORT picks the canvas port, 3000 by default.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

from nodejs_wheel import node, npm

ENGINE_DIR = Path(__file__).resolve().parent / "engine"
ENGINE_PACKAGE = "mcp-excalidraw-server"
DEFAULT_PORT = 3000
HIGHEST_PORT = 65535

REFUSED = {
    "share": "`share` uploads the scene to excalidraw.com. Publishing is the user's call; export a file instead.",
    "install-skill": "`install-skill` would install a second skill beside this one. This skill already covers it.",
}


class RefusedError(Exception):
    """A command this script will not pass on, with the reason to show."""


def check_arguments(args: list[str]) -> None:
    """Raise `RefusedError` for anything the engine may not be asked to do from here."""
    if not args:
        return
    command, rest = args[0], args[1:]
    if command in REFUSED:
        raise RefusedError(REFUSED[command])
    for index, arg in enumerate(rest):
        if arg == "--url" or arg.startswith("--url="):
            raise RefusedError(
                "`--url` is not accepted; the canvas always runs on loopback. Set EXCALIDRAW_PORT instead."
            )
        if command != "export":
            continue
        following = rest[index + 1] if index + 1 < len(rest) else ""
        out = arg.split("=", 1)[1] if arg.startswith("--out=") else following if arg == "--out" else ""
        if out.lower().endswith(".md"):
            raise RefusedError(f"`{out}` would be the Obsidian `.excalidraw.md` wrapper; use a `.excalidraw` path.")
        fmt = arg.split("=", 1)[1] if arg.startswith("--format=") else following if arg == "--format" else ""
        if fmt == "obsidian":
            raise RefusedError("the Obsidian format is not exported here; write plain `.excalidraw` JSON.")


def canvas_port(environ: dict[str, str]) -> int:
    raw = environ.get("EXCALIDRAW_PORT", "").strip()
    if not raw:
        return DEFAULT_PORT
    if not raw.isdigit() or not 0 < int(raw) <= HIGHEST_PORT:
        raise RefusedError(f"EXCALIDRAW_PORT must be a port number, not {raw!r}.")
    return int(raw)


def engine_environment(environ: dict[str, str]) -> dict[str, str]:
    """The environment the engine runs in: the caller's, with the canvas pinned to loopback.

    Set explicitly rather than defaulted, because the engine loads a `.env` from
    the working directory and that file must not be able to move the canvas.
    """
    port = canvas_port(environ)
    return {
        **environ,
        "EXPRESS_SERVER_URL": f"http://127.0.0.1:{port}",
        "HOST": "127.0.0.1",
        "PORT": str(port),
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
    """Install the pinned engine once, and return the directory holding it.

    The install happens in a scratch directory beside the target and is moved
    into place only once complete, so an interrupted run or two agents starting
    at once never leave a half-installed engine that later runs would trust.
    """
    root = cache_root(environ)
    target = root / engine_key()
    if engine_entry(target).is_file():
        return target

    root.mkdir(parents=True, exist_ok=True)
    print(
        "excalidraw: installing the drawing engine (first run only; a few hundred MB, about a minute)...",
        file=sys.stderr,
    )
    scratch = Path(tempfile.mkdtemp(prefix=".install-", dir=root))
    try:
        for name in ("package.json", "package-lock.json"):
            shutil.copy2(ENGINE_DIR / name, scratch / name)
        # `npm ci` installs exactly the lock file and refuses if it disagrees with
        # package.json; `--ignore-scripts` keeps every dependency's install hook
        # from running, which the engine does not need.
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
    return target


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        args = ["help"]
    try:
        check_arguments(args)
        environ = engine_environment(dict(os.environ))
    except RefusedError as refusal:
        print(f"excalidraw: refused: {refusal}", file=sys.stderr)
        return 2

    engine = ensure_engine(environ)
    return node([str(engine_entry(engine)), *args], env=environ)


if __name__ == "__main__":
    raise SystemExit(main())
