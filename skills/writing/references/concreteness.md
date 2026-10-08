# Concreteness: the behaviour, not its label

The imperatives are in `SKILL.md`. This page carries the reasoning and the worked
examples, for when a judgement call is close.

Live page:
<https://ftschindler.github.io/knowledge/principles/name_the_concrete_behaviour_not_its_abstract_label/>

## The claim

A sentence can pass every honesty check - settled-fact tense, no hype, no
throat-clearing - and still force a re-read, because it names an abstract
category instead of the behaviour the reader can observe.

Clarity is a separate axis from honesty. [Voice](voice.md) guards against
dishonest language; this guards against jargon-dense honest language.

## The failure it prevents

> Both security-relevant defaults fail closed: an unconfigured bundle is sealed
> and read-only until you open each axis deliberately.

Every word is honest and calm, and it needs three reads. It stacks four
abstractions - *fail closed*, *sealed*, *read-only*, *open each axis* - over
exactly two concrete facts: nobody may reference it, nobody may write to it. The
reader unpacks each metaphor back into the two behaviours the prose could have
stated directly.

## Why it costs the reader

A label is a compression of a behaviour, and compression only helps a reader who
already holds the codebook. A first-time reader decompresses every term, and
stacked terms multiply the cost. Naming the behaviour skips the decode step.

When the concrete form is already on screen - in the table directly above - the
abstraction adds nothing but a second thing to reconcile.

## Abstract label, and the rewrite

| Abstraction-stacked (honest but opaque) | Concrete behaviour (honest and clear) |
| --- | --- |
| "Both defaults fail closed: an unconfigured bundle is sealed and read-only." | "A new bundle can't be referenced and can't be written to until you say so." |
| "The gate is idempotent across re-invocation." | "Running it twice changes nothing the second time." |
| "Reads are unrestricted; the boundary is the write path." | "Any bundle can be read; only writing is checked." |

## The revision pass

For each explanatory sentence, ask what the reader actually sees happen, and
whether the sentence says that or a category name for it. Grep your own coined
abstractions - `sealed`, `fail-closed`, `gated`, `idempotent` - and confirm each
is either preceded by its concrete form or genuinely earning reuse later. Flag
any sentence stacking two or more labels.

## Where it came from

Earned rewriting a defaults sentence a reader had to read three times. The fix
was to name the two behaviours already sitting in the field table above it.
