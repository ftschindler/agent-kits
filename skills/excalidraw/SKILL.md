---
name: excalidraw
description: Draw an Excalidraw diagram and save it as a `.excalidraw` file. Use when asked to sketch, draw, diagram or visualise something - an architecture, a flow, a set of relationships, or what was just learned - or to change an existing `.excalidraw` file. Needs only `uv`; the drawing engine installs itself on first use.
---

# Drawing Excalidraw diagrams

You build a diagram one command at a time, look at it, fix it, and end with a
plain `.excalidraw` file that opens in Excalidraw, VS Code or Obsidian.

## Where the file goes

Where the user says. Otherwise in the current directory, named for what it
shows: `release_flow.excalidraw`, not `diagram.excalidraw`.

When the file is going into a directory that documents its own conventions for
diagrams - an `AGENTS.md`, `CONTRIBUTING.md` or `editing_conventions.md` that
says where they live and how they are named - follow those.

Screenshots are for checking your work. Do not leave them beside the diagram.

## The script

Every command goes through `scripts/excalidraw.py`, beside this file, run with
`uv run --script`. From here on, `excalidraw` means:

```sh
uv run --script <this skill's directory>/scripts/excalidraw.py
```

The first run installs the engine and takes a minute or so. That is not a hang.

Each call names the file first and the command second:

```sh
excalidraw <file>.excalidraw <command> [args]
```

The file is the drawing. A command that changes the drawing saves it back to the
file; a file that does not exist yet starts empty. Nothing else is kept between
calls, so there is nothing to start, stop or clean up.

`excalidraw help` lists the commands, and `excalidraw help <command>` explains
one. Results come back as JSON on stdout, except `describe`, which is text.

## Drawing a diagram

1. **Plan the layout before writing any JSON.** Decide what the boxes are, how
   they group, and which direction the flow reads. Sketch the coordinates:
   tiers 100 px apart, siblings at least 50 px apart.
2. **Add the shapes and arrows in one call**, as a JSON array on stdin:

   ```sh
   excalidraw release_flow.excalidraw add <<'EOF'
   [
     {"id": "source", "type": "rectangle", "x": 0, "y": 0, "width": 180, "height": 60, "text": "Source"},
     {"id": "sink", "type": "rectangle", "x": 300, "y": 0, "width": 180, "height": 60, "text": "Sink"},
     {"type": "arrow", "x": 0, "y": 0, "startElementId": "source", "endElementId": "sink"}
   ]
   EOF
   ```

3. **Look at it.** `excalidraw <file> screenshot --out <somewhere temporary>.png`
   writes an image; open it. `excalidraw <file> describe` lists every element
   with its id, position and label, which is what you need to change one.
4. **Fix what you see, then look again.** Change one element with
   `excalidraw <file> update <id> --set '{"width": 240}'`, or several at once
   with `excalidraw <file> apply`. Repeat until the checklist below passes.

To change an existing diagram, start at step 3 with its file.

## Before you call it done

Check the screenshot, not the JSON:

- **Every label is fully visible.** A cut-off label means the shape is too
  small. Width `max(160, 12 × characters)` keeps a label on one line.
- **Nothing overlaps.** A box drawn around a group contains its members with
  room to spare.
- **No arrow crosses an unrelated shape.** Route it around with a waypoint in
  `points`, or set `"elbowed": true`.
- **Text is readable.** Font size 16 or more, 20 for a title.
- **It says one thing.** A diagram that needs a paragraph to explain is two
  diagrams, or a list.

## Element notes

- A shape's `text` becomes its label, centred inside it. Arrows bound with
  `startElementId` and `endElementId` follow their shapes when those move.
- A large box that groups others gets no `text`: its label would land in the
  middle, on top of its contents. Put a separate `text` element at its top
  corner instead.
- Label arrows only where the relationship needs naming, in a word or two.
- `"fillStyle": "solid"` with a pale `backgroundColor` and a darker
  `strokeColor` reads cleanly. `"strokeStyle": "dashed"` marks a boundary.
- Element types are `rectangle`, `ellipse`, `diamond`, `arrow`, `line` and
  `text`.

## When something fails

- **`excalidraw: refused`:** the script will not do that. Read the reason and
  tell the user rather than trying another way to do it.
- **Any other error:** the file is unchanged, because a failed command saves
  nothing. Read the message, fix the input and run the command again.

The engine is
[mcp-excalidraw-server](https://github.com/yctimlin/mcp_excalidraw), at the
version pinned in `scripts/engine/package-lock.json`.
