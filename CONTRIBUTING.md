# Contributing

## Prerequisites

- [uv](https://docs.astral.sh/uv/), which provides `uv` and `uvx`
- [Node.js](https://nodejs.org) 24+, which provides `node`, `npm` and `npx`
- `git`

[make](https://en.wikipedia.org/wiki/Make_(software)) is an optional
convenience. Every target is a single `uv run` line, precisely so that the
make-less path is not a second, rotting set of instructions: look the line up in
the [Makefile](Makefile) and run it directly.

Everything here works on Linux, macOS and Windows, and both Linux and Windows are
tested in CI.

```sh
git clone https://github.com/ftschindler/agent-kits.git
cd agent-kits
make bootstrap
```

## Authoring a kit

### A skill

```text
skills/<name>/
  SKILL.md        # required, with `name` and `description` frontmatter
  references/     # optional: documents the skill reads when it needs them
  scripts/        # optional: executables the skill runs
```

**`name` must equal the directory name.** They are two different handles and both
travel: the directory is what a subscription names, the frontmatter is what the
part installs as. Where they disagree, `akit add agent-kits <dir>` resolves and
then lands somewhere else.

**`description` says when to use the skill, not what it is.** It is the only text
a model sees before deciding whether to open the file, so it carries the trigger
conditions: *"Use when drafting or revising prose, or when a draft reads as
promotional"*.

**Nothing sits more than three levels under `skills/`.** That is as far as
discovery walks. `skills/writing/` and `skills/prose/writing/` both resolve, so
categories can arrive later without a migration; a fourth level cannot be found
at all.

### A rule

```text
rules/<name>.md   # frontmatter with a `description`, then the instruction
```

A rule goes into every prompt without being opened, so it is short, and it is the
thing you would otherwise paste into four harness config files.

**`description` is required, even though a rule is identified by its filename.**
GitHub Copilot's `.github/instructions/` attaches a file by matching its
`description` or its `applyTo` glob, so a rule without one is discovered and then
never loaded - which looks exactly like a rule that is being ignored.

### Python beside a skill

A script carries its own dependencies in a
[PEP 723](https://peps.python.org/pep-0723/) header and is run with
`uv run --script`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
```

There is no repository-level dependency list and no lockfile. A skill is
installed by copying its directory, so anything it needs has to be inside the
files that get copied - and a subscriber then needs `uv` and nothing else.

`.scripts/run-tests.py` collects those headers from `skills/` and `.scripts/` and
passes them to the test run, so a new dependency needs no second declaration
anywhere.

## Tests

Three layers, each one `make` target and one CI job:

```sh
make test_conformance   # every kit is shaped the way akit discovers one
make test_scripts       # the Python under .scripts/ and inside the skills
make test_agent         # install the kits into a real agent and talk to it
make test               # all three
```

**Conformance** reads what is committed: frontmatter, names, depth. It is the
layer that catches a skill renamed in one place and not the other, which is
otherwise a part that silently does not exist on somebody else's machine.

**Scripts** unit-tests the guards against crafted trees in a temp directory. A
guard exercised only against a conformant repository passes just as happily once
it has stopped checking anything, so the tests that matter here are the ones
asserting a malformed kit is *caught*.

**Agent** is end to end: it builds a throwaway
[opencode](https://opencode.ai) in a redirected `HOME`, installs the kits into it
the way a subscriber would, sends it a message and reads the reply. It needs the
network and a few minutes, and it is the only layer that can tell you an
instruction is unfollowable. No API key: the pinned opencode's default model is
free to use.

When one fails, the agent is kept and the command to enter its world is printed
with the failure. `make agent` builds one to poke at by hand.

### Testing a kit you have written

A skill test asserts behaviour, not wording. Give the skill an instruction with
an observable consequence, ask the agent something that should trigger it, and
check the transcript:

```python
result = kit_agent.run("Revise this: our powerful tool makes testing effortless.")
assert "powerful" not in result.text.lower()
```

Keep the trigger mundane. An earlier test in the sibling repository asked an
agent to "report the canary token", which reads as an attempt to extract a
secret: the model declined, and the test measured safety training rather than
skill discovery.

## The guards

`make check` runs everything below, and CI runs exactly the same command, so a
green local run means a green pipeline.

Each hook is pinned to a frozen SHA and bumped by Dependabot as an explicit diff.
Auto-fixers are ordered so general text hygiene runs last and cannot re-dirty a
content formatter's output.

Three of them are ours:

- **kit-layout** - the conformance rules above, at commit time rather than
  review time.
- **support-script-tests** - the `scripts` layer, when a guard or a test changes.
- **no-symlinks** - a symlink is committed as a blob holding its target path, and
  a Windows clone without developer mode writes that path out as an ordinary text
  file. The link does not break loudly; it becomes a one-line document that every
  reader downstream takes as the content. Invisible on the machine that
  introduces it, which is why it is a guard and not a preference.

## Using these kits while you work on them

Until akit can render from a working tree, link each skill into the directory
every harness reads, so an edit here is live:

```sh
mkdir -p ~/.agents/skills
for kit in skills/*/; do ln -s "${PWD}/${kit%/}" ~/.agents/skills/; done
```

In PowerShell, where a symlink needs developer mode or an elevated shell (without
either, use `Copy-Item -Recurse` and re-copy after each edit):

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Get-ChildItem -Directory skills | ForEach-Object {
  New-Item -ItemType SymbolicLink -Path "$HOME\.agents\skills\$($_.Name)" -Target $_.FullName
}
```

Remove any previously installed copy first. These links live in your home
directory and are never committed; a symlink *inside* the repository is refused
by a hook, for the reason above.
