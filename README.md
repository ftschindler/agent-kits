# agent-kits

Felix's agent kits: **skills** an agent can open, and **rules** that go into every
prompt. Subscribe to them with
[akit](https://github.com/ftschindler/federated-agent-kits), which renders them
into whichever directory your harness reads.

```sh
uvx --from federated-agent-kits akit add ftschindler/agent-kits writing
uvx --from federated-agent-kits akit render
```

This repository is an ordinary git repository and knows nothing about who has
subscribed to it. Clone it, copy a directory out of it by hand, or point
`npx skills add` at it; all three work.

## What is in here

| Directory | Holds | Found by |
| --- | --- | --- |
| `skills/<name>/` | a `SKILL.md`, plus the `references/` and `scripts/` it reads | akit, `npx skills add`, any harness reading `.agents/skills/` |
| `rules/<name>.md` | one instruction that applies without being opened | akit |

`agents/` arrives with the first agent definition.

## Working on it

```sh
make bootstrap   # install the pre-commit hooks into this clone
make check       # the full guard suite, which is what CI runs
make test        # every test layer
```

[CONTRIBUTING.md](CONTRIBUTING.md) covers authoring a kit, the three test layers
and what each guard is for.

## Licence

[MIT](LICENSE).
