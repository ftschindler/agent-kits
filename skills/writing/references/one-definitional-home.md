# One definitional home per concept

Read this when drafting anything longer than a screen. It operates at document
scope, above the section-scope and sentence-scope rules in [document
shape](document-shape.md).

Live page:
<https://ftschindler.github.io/knowledge/principles/give_every_cross_cutting_concept_one_definitional_home/>

## The claim

A concept that surfaces in several places - a trust model, a security invariant,
a naming convention - is defined in exactly one section. Every other mention
references that home rather than restating it.

## The failure it prevents

Following only local rules produces text that is correct in isolation at every
site and wrong in aggregate. A concept stated in seven places, each a clean and
well-voiced sentence, makes the reader assemble the whole from fragments, and no
single place can be pointed at as the definition.

Worse, a later sentence says "the trust model" as if it had been defined when it
never was. The phrase orbits a centre of gravity that does not exist.

## The rules

**Name the recurring concept.** Before finalising, list the ideas that appear
more than twice. Each is a candidate for a single home.

**Pick the home.** Usually the first place the reader needs the *full* idea, not
the first place it is touched. Give it a heading if it earns one.

**Demote every other mention to a reference.** State the local slice needed
there, then link to the home. A field table names the field and its default; the
why lives at the home. A diagram may label the concept; its definition does not
travel with it.

**Check the back-references resolve.** Any sentence saying "the X" follows X's
definition, or links forward to it. A named concept with no reachable definition
is the tell that this rule was skipped.

## Why one home

A reader looking for "how does this actually prevent leaks?" should find one
section that owns the answer, not seven partial answers to reconstruct. One home
is also one place to edit when the concept changes, which is the dividend
centralising coupling pays in code.

## Smeared, and the rewrite

| Smeared (locally correct, globally scattered) | Homed (one definition, N references) |
| --- | --- |
| Trust model restated in getting-started, a field table, two diagrams and the rationale | One "Trust model" section; the table says "default `[]`", the diagram labels "read-all", both defer the why |
| "The asymmetry is the trust model: you may learn from anything, but..." | "This read-all/write-one split is the trust model in action", linking to it |
| A caveat's honest limits buried in a note far from where the concept is defined | The limit lives in the concept's home, under a "What this does not guarantee" line |

## The review pass

Grep for each recurring concept's keywords. Where it is *explained* rather than
merely referenced in more than one place, collapse the extras into references.
Confirm every "the `<concept>`" phrase has a definition it can reach.

## Where it came from

Earned rewriting a README that stated its trust model seven times. Consolidating
to one section made a forward reference that had pointed at nothing finally point
at something.
