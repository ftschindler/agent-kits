---
name: writing
description: Apply Felix's house prose style to anything written for a reader - documentation, READMEs, wiki concepts, commit messages, PR descriptions, reports, emails, and chat replies. Use when drafting or revising prose, when asked to make writing clearer or less like AI, or when a draft reads as promotional, jargon-dense or too dense to follow. Not for code itself.
---

# House prose style

Three rules, on three different axes. A draft can pass two and fail the third,
so check all three.

| Axis | Guards against | The question |
| --- | --- | --- |
| Voice | dishonest language | Is this overselling? |
| Concreteness | jargon-dense honest language | Is this the right word? |
| Pace | correct language delivered too fast | How much arrives at once? |

The imperatives below are enough for the ordinary case. When a judgement call
is close, the reasoning and the worked examples for that axis sit beside this
file:

- [references/voice.md](references/voice.md)
- [references/concreteness.md](references/concreteness.md)
- [references/pace.md](references/pace.md)

A harness may also carry a digest of the imperatives in its `AGENTS.md`, so
that replies are styled without loading anything. This skill is that digest's
expansion. Each reference page links to its live version in the public wiki,
which is the authority over all three forms.

## When a repository disagrees, the repository wins

Check for `AGENTS.md`, `CONTRIBUTING.md` or an `editing_conventions.md` before
writing into someone's repository. Where it names a different style guide,
follow that one and drop this skill.

This skill is the default for prose with no other owner: chat replies, commit
messages, emails, and any repository that has not said otherwise.

## Voice

Narrate behaviour as settled fact in the present tense. *"This downloads
Miniforge, installs it locally, and verifies all imports"*, one sentence, four
verbs, no hedging.

- **"We" for choices the project made**, never for hype. *"We ship tests
  which..."*, never *"our powerful setup"*.
- **"You" to hand over an action**, never to flatter. *"Each time you open a
  new shell:"*.
- **Volunteer the inconvenient truth, with numbers.** *"required around 52GB
  and 150h on our hardware"*. Say `similar`, not `identical`.
- **Hedges map to real variance.** `around` and `roughly` are precise
  admissions about a stochastic process, not nervous filler.
- **Asides go in parentheticals and blockquotes.** The happy path stays the
  main line.
- **No throat-clearing.** Never open with *"In order to"*, *"It is important
  to note"*, *"As you can see"*, *"Simply"* or *"Just"*. Open with the subject.
- **Earn every exclamation mark.** At most one per document, on the genuinely
  surprising fact.

Banned outright: `seamless`, `effortless`, `powerful`, `robust`,
`cutting-edge`, `revolutionary`, *"in no time"*, *"will ensure"*, `delve`,
`tapestry`, *"testament to"*, and the *"it's not just X, it's Y"*
construction.

## Concreteness

State what the reader can observe, before naming any category for it.

- *"A new bundle can't be referenced and can't be written to"* beats *"an
  unconfigured bundle is sealed and read-only"*.
- **Introduce a coined label only after its behaviour has landed**, and only if
  it earns reuse later.
- **Do not re-encode what is already on screen.** If `writable: false` sits in
  the table above, the prose says *"can't be written to"*, not *"read-only"*.
- **One abstraction per sentence at most.** Two stacked categories in one
  clause is what forces the re-read.

## Pace

- **Restate the question in one line before answering.** The reader may not
  have the thread loaded.
- **One idea per sentence, one point per paragraph.** Two or three sentences
  per paragraph. A sentence carrying three subordinate clauses is three
  sentences wearing a coat.
- **Label options by what they mean.** *"Don't have several styles"* beats
  *"converge the bundles on one house style"*.
- **Lead each option with the recommendation, then the plain reason.**
- **Keep cross-references out of the body.** Collect every *(see below)* into
  one line at the end.
- **Bold the claim, not the keywords.** One bold sentence per section.
- **One insight per reply, at the end.** An insight in every paragraph means
  none of them lands.
- **Do not recap what you just said.** Stop when the answer is delivered.

## It is not warmth

Warmth is the cheapest register to imitate, so anything asked to be warm
reaches for enthusiasm, second-person chumminess and exclamation, which is
precisely the prose this style exists to avoid. What makes writing read as
human is specificity and restraint: naming what was given up, quantifying
where possible, declining to hedge. Concreteness is expensive to fake; warmth
is free.

## Mechanics

British English throughout: "ise" endings, "our" endings, "whilst" rather than
"while", no Oxford comma.

Two characters are banned because they are awkward to type and inconsistent to
grep: the em dash (U+2014), where `-` serves, and the ellipsis (U+2026), where
`...` serves. Both are allowed inside code blocks, which quote something
else's syntax.

Avoid thematic breaks (`---`) in markdown. Headings already separate sections.

## Structure, for anything longer than a screen

Two further principles govern shape rather than sentences. The short form:
lead each section with the runnable command and demote the why; and define a
recurring concept in exactly one section, referencing it everywhere else.

Read them in full when drafting a README, a runbook or a design document:

- [references/document-shape.md](references/document-shape.md)
- [references/one-definitional-home.md](references/one-definitional-home.md)

## Revising a draft

Two passes, in this order.

1. **Grep for the banned list above**, plus `simply`, `just`, bare
   superlatives, future-promise framing and more than one `!`. Rewrite each hit
   toward settled-fact present tense with a quantified cost.
2. **Read a paragraph and count the ideas.** More than one, split it. Then ask
   of each explanatory sentence what the reader actually sees happen, and
   whether the sentence says that or a category name for it.

In a repository that has the `prose-tells` pre-commit hook, the first pass is
mechanical: run `prek run prose-tells --all-files`. The second pass is
judgement and stays manual.
