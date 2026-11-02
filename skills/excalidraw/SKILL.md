---
name: excalidraw
description: Draw an Excalidraw diagram and save it as a `.excalidraw` file. Use when asked to sketch, draw, diagram or visualise something - an architecture, a flow, a set of relationships, or what was just learned - or to change an existing `.excalidraw` file. Needs only `uv`; the drawing engine installs itself on first use.
---

# Drawing Excalidraw diagrams

You draw on a local canvas through one script, look at what you drew, fix it,
and export the result as a plain `.excalidraw` file. The file is the deliverable;
everything else is scaffolding.

## Where the file goes is the repository's call

Before drawing into someone's repository, check its `AGENTS.md`,
`CONTRIBUTING.md` or an `editing_conventions.md` for where diagrams live, how
they are named and how a page embeds one. Follow that. Where nothing is said,
put the diagram beside the page it illustrates, name it after that page, and
embed it with a Markdown image: `![What it shows](page_diagram.excalidraw)`.

Commit the `.excalidraw` file and nothing else. Screenshots are for you to check
your work, not for the repository.

## The script

Every command goes through `scripts/excalidraw.py`, beside this file, run with
`uv run --script`. From here on, `excalidraw` means:

```sh
uv run --script <this skill's directory>/scripts/excalidraw.py
```

The first run installs the engine and takes a minute or so. That is not a hang.

`excalidraw help` lists every command and `excalidraw help <command>` explains
one. Results come back as JSON on stdout, except `describe`, which is text.

The script refuses `share`, which uploads the scene to excalidraw.com, and any
export to `.excalidraw.md`. Do not look for a way around either. If the user
wants a link or the Obsidian format, tell them and let them do it.

## Drawing a diagram

1. **Plan the layout before writing any JSON.** Decide what the boxes are, how
   they group, and which direction the flow reads. Sketch the coordinates:
   tiers 100 px apart, siblings at least 50 px apart.
2. **Start clean:** `excalidraw clear --yes`. The canvas outlives your session,
   so it may hold someone else's last drawing.
3. **Add the shapes and arrows in one call**, as a JSON array on stdin:

   ```sh
   excalidraw add <<'EOF'
   [
     {"id": "source", "type": "rectangle", "x": 0, "y": 0, "width": 180, "height": 60, "text": "Source"},
     {"id": "sink", "type": "rectangle", "x": 300, "y": 0, "width": 180, "height": 60, "text": "Sink"},
     {"type": "arrow", "x": 0, "y": 0, "startElementId": "source", "endElementId": "sink"}
   ]
   EOF
   ```

4. **Look at it.** `excalidraw screenshot` writes a PNG to a temporary file and
   prints its path; open that image. `excalidraw describe` lists every element
   with its id, position and label, which is what you need to change one.
5. **Fix what you see, then look again.** Change one element with
   `excalidraw update <id> --set '{"width": 240}'`, or several at once with
   `excalidraw apply`. Repeat until the checklist below passes.
6. **Export:** `excalidraw export --out <path>.excalidraw`.
7. **Stop the canvas:** `excalidraw stop`.

To change an existing diagram, start with
`excalidraw import <file>.excalidraw --replace` instead of `clear`, then
continue from step 4 and export over the same file.

## Before you export

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

- **Exit code 3, canvas unreachable:** usually another program holds the port.
  Set `EXCALIDRAW_PORT` to a free one and retry.
- **Exit code 4, browser required:** only `mermaid` needs an open browser tab.
  Draw the elements directly instead.
- **`excalidraw: refused`:** the script will not do that. Read the reason and
  tell the user rather than trying another route.

The engine is
[mcp-excalidraw-server](https://github.com/yctimlin/mcp_excalidraw), at the
version pinned in `scripts/engine/package-lock.json`.
