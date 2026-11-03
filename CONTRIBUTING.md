# Contributing

## Prerequisites

- [uv](https://docs.astral.sh/uv/), which provides `uv` and `uvx`
- [Node.js](https://nodejs.org) 24+, which provides `node`, `npm` and `npx`
- `git`
- [opencode](https://opencode.ai), logged in to a provider, to record evidence
  for a kit you change

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

**A reference ships beside the skill rather than as a URL.** A `SKILL.md` that
links out to the web is a `SKILL.md` whose reasoning does not get read: in
practice a model follows a relative path and does not open a link. So the long
form lives in `references/`, as a plain digest with no frontmatter, and names the
page it was distilled from so the authority stays traceable. Three conformance
tests hold that shape: no frontmatter, linked from its own `SKILL.md`, and
carrying the live URL.

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

Two offline layers, each one `make` target and one CI job, and a third that runs
on your machine:

```sh
make test_conformance   # every kit is shaped the way akit discovers one,
                        # and its evidence still describes it
make test_scripts       # the Python under .scripts/ and inside the skills
make test               # both
make record_evidence KIT=<name>   # ask a real assistant, write the evidence
```

**Conformance** reads what is committed: frontmatter, names, depth. It is the
layer that catches a skill renamed in one place and not the other, which is
otherwise a part that silently does not exist on somebody else's machine.

**Scripts** unit-tests the guards against crafted trees in a temp directory. A
guard exercised only against a conformant repository passes just as happily once
it has stopped checking anything, so the tests that matter here are the ones
asserting a malformed kit is *caught*.

### Evidence: the layer that talks to an assistant

Both layers above read text. Neither can tell you an instruction is one a model
will not follow, which is the failure a kit actually has: a skill that is
discovered, opened and then ignored passes every check in this repository.

This repository used to answer that by building a throwaway assistant in CI on
opencode's free models. From GitHub's runners those models are out of quota, and
opencode waits on the error instead of exiting, so every run hung until the job
timed out ([#12](https://github.com/ftschindler/agent-kits/issues/12)). So the
run now happens on your own machine, against the assistant you have already
authenticated, and what CI sees is the recording.

```sh
make record_evidence KIT=writing RECORD_ARGS="--model github-copilot/claude-sonnet-5"
```

That asks the questions in `tests/probes/<kit>.json` of a disposable agent
holding only that kit, checks each answer against the assertions beside the
question, and writes the prompt, the scrubbed reply and the outcomes into
`tests/evidence/<kit>.json`. The agent is a temp HOME with your opencode
credentials copied in and nothing else, so the reply is a reaction to the kit
rather than to whatever else you have installed.

**A probe asserts on substrings, not on quality.** `contains_none`,
`contains_all` and `contains_any`, each with a name saying what it is for. That
is blunt on purpose: it catches the kit being ignored, which is the failure
worth automating, and leaves judgement to review.

**Keep the trigger mundane.** An earlier probe asked an agent to "report the
canary token", which reads as an attempt to extract a secret: the model
declined, and the probe measured safety training rather than skill discovery.

**A failing recording is committable.** A kit that does not work is better
described than hidden, so `outcome: "fail"` is written out and the conformance
test then fails on it by name.

`.scripts/check_evidence.py` is the offline half, and runs in CI and at commit
time. It cannot tell you the run happened; it tells you the recording still
describes what is committed. Every file of the kit is hashed, and the *set* of
files is compared too, so adding a reference without re-recording is caught as
well: a hash-only check would miss exactly the content a skill loads when it
matters.

So editing a kit means re-recording it. The hook will say so.

## The guards

`make check` runs everything below, and CI runs exactly the same command, so a
green local run means a green pipeline.

Each hook is pinned to a frozen SHA and bumped by Dependabot as an explicit diff.
Auto-fixers are ordered so general text hygiene runs last and cannot re-dirty a
content formatter's output.

Four of them are ours:

- **kit-layout** - the conformance rules above, at commit time rather than
  review time.
- **kit-evidence** - the evidence rules above, so a kit edited after its
  recording is caught before the commit lands rather than in review.
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
