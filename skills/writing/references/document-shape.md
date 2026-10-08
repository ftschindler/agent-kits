# Document shape: lead with the action

Read this when drafting a README, a runbook or a contributing guide. It governs
what appears where and in what order, which is a different question from how a
sentence reads.

Live page:
<https://ftschindler.github.io/knowledge/principles/structure_docs_as_the_readers_task_path_lead_with_action_defer_rationale/>

## The claim

A task-oriented document is organised by the reader's actual path through the
task, not by the author's mental model of the system. At each step, lead with
what the reader must **do** - the runnable command - and defer the why to a
following aside or a nested section they descend into only if they care.

**Not for reference docs.** Their reader arrives to look something up and is
better served by dense tables.

## The rules

**Lead with the action, defer the rationale.** At a section's entry, the first
thing is what to do, not the causal theory behind it. A requirements table whose
"why we chose Node" reasoning greets a first-time contributor delivers rationale
before anybody wanted it. State *"we require uv and Node"*; move *why uv cannot
provide Node* to a later line or a `>` aside. This is [the aside
rule](voice.md) raised from the sentence to the section.

**Follow the task's real order.** The spine is the contributor's actual sequence:
clone, bootstrap, run, inspect, each step copy-pasteable rather than prose
describing a command. Do not start at step two - the classic omission is jumping
to "install the hooks" without the `git clone` before it.

**Explode caveats into navigable structure.** When one path carries a mechanism
worth explaining, give it its own heading and reach it by a link from the happy
path. Sequence multi-step behaviour as a bulleted list, not a comma-spliced
sentence. The happy path stays a clean spine and depth lives one click down.

## Why density and walkability trade off

A packed table with a "Used for / Notes" column puts everything on one screen.
That is optimal for somebody re-checking a fact and hostile to somebody doing the
task for the first time, who now reads rationale to reach the one command they
need.

Task docs are read while acting. The reader wants the next command, then the
option to go deeper. Ordering by the task path means the fast reader is never
blocked and the curious reader is never denied.

## Author's shape, and the rewrite

| Reference shape (author's model) | Task-path shape (reader's path) |
| --- | --- |
| A requirements table leading with per-tool rationale | *"We require uv and Node"* first; why-this-tool demoted to a `>` aside |
| "Install the git hooks:" as the opening step | `git clone ... && cd ... && make bootstrap`, the real first step, runnable |
| One paragraph and two blockquotes covering the whole e2e harness | `make test_skills` first; the harness mechanism factored into a linked section, its steps a bulleted list |

## The review pass

Walk the document as the reader. Can a first-timer reach the first command
without reading rationale? Does the heading order match the doing order? Is any
paragraph a wall of caveats that should be a sub-section plus a link?
