# Voice: calm, quantified, settled fact

The imperatives are in `SKILL.md`. This page carries the reasoning and the worked
examples, for when a judgement call is close.

Live page:
<https://ftschindler.github.io/knowledge/principles/write_in_a_calm_quantified_settled_fact_voice_not_a_promotional_one/>

## The claim

Technical prose reads like a maintainer standing next to the reader, narrating
what the machine does as settled fact, volunteering the real costs, and handing
over actions. Not like a landing page selling the tool.

## Why this register and not another

This is the negative image of default LLM prose, which is the whole point. An
agent told "write docs" reaches for *"This powerful setup script seamlessly
handles everything, ensuring a smooth experience - simply run the command and
you'll be up and running in no time!"*

That register is untrustworthy because it hides cost and overstates certainty.
The maintainer voice is pleasant to read because it respects the reader: it
states what happens, admits what varies, and never sells.

## The rules, with what each one is for

**Settled-fact present tense.** *"This downloads Miniforge, installs it locally,
creates the environment, and verifies all imports"*: one sentence, four verbs, no
hedging. A future promise is a claim about a run that has not happened.

**"We" for choices the project made**, never for hype. *"We ship tests
which..."*, *"We recommend prek"*. In a walkthrough, "we" may also be a teaching
narrator guiding the reader through a task - *"We can also run individual test
layers"*. The bar that register still has to clear is guiding, never selling.

**"You" to hand over an action or an expectation.** *"Each time you open a new
shell:"*, *"you will also need latexmk"*, *"This should leave you with
output/"*. Never to flatter.

**Honesty as courtesy, quantified.** *"regenerates similar data, though timings
may differ"*, *"required around 52GB and 150h on our hardware"*. `similar`, not
`identical`.

**Hedges map to real variance.** `similar`, `around` and `roughly` are precise
admissions about a stochastic process. *"This may or may not potentially"* is
nervous filler, and the two are not the same thing.

**Asides go in parentheticals and blockquotes.** The happy path is the prose;
cost, caveats and escape hatches live in `>` notes and `(...)`.

**No throat-clearing**, and **at most one exclamation mark**, on the genuinely
surprising fact: *"150h of time on our target hardware!"*

## Slop, and the rewrite

| Slop tell | Rewrite in this voice |
| --- | --- |
| "This will seamlessly set up your entire environment." | "This downloads Miniforge, installs it locally, and verifies all imports." |
| "Simply run the command and you're good to go!" | "Each time you open a new shell: `source 01_activate_env.bash`." |
| "Our powerful test suite ensures everything works." | "We ship tests which run the code on a simplified setup and compare against expected results." |
| "You'll be up and running in no time." | "Running them required around 52GB and 150h on our target hardware." |
| "This produces identical results." | "This regenerates similar data, though timings and speedup may differ." |

## Where it came from

Distilled from the companion-code READMEs of the 2026 pyMOR paper, whose voice
this is.
