"""The writing kit, tested by giving a real agent a draft to fix.

The conformance layer proves the skill is discoverable and the rule carries a
description. Neither says the instructions can be followed, which is the only
question that matters about a kit whose entire output is a model's behaviour.

What is asserted is the mechanical half of the style: the banned words. Pace and
concreteness are judgement, and a test that scored them would be measuring the
model it ran against rather than the skill.
"""

from __future__ import annotations

import pytest
from disposable_agent import DisposableAgent

pytestmark = pytest.mark.agent

# A draft built from the skill's own banned list, in the register it exists to
# remove. Every one of these appears in the "Banned outright" line of SKILL.md.
PROMOTIONAL_DRAFT = (
    "Our powerful and robust new tool delivers a seamless, effortless experience. "
    "It is a testament to the cutting-edge engineering of our team, and it will "
    "ensure your pipelines are green in no time!"
)
BANNED = ("powerful", "robust", "seamless", "effortless", "cutting-edge", "testament to", "in no time")


def test_the_skill_is_installed_under_the_name_a_subscriber_asks_for(kit_agent: DisposableAgent) -> None:
    """Installed from skills/ exactly as akit or `npx skills add` would copy it."""
    assert (kit_agent.agents_skills / "writing" / "SKILL.md").is_file()


def test_the_skill_strips_the_words_it_bans(kit_agent: DisposableAgent) -> None:
    """A draft written entirely in the register the skill rejects comes back without it."""
    result = kit_agent.run(
        "Revise the following so it follows this project's house writing style. "
        "Reply with the revised text only.\n\n"
        f"{PROMOTIONAL_DRAFT}"
    )

    assert result.returncode == 0, f"opencode exited {result.returncode}\n{result.stderr}"
    assert result.text.strip(), "the agent replied with nothing"

    lowered = result.text.lower()
    survivors = [word for word in BANNED if word in lowered]
    assert not survivors, (
        f"the writing skill did not reach the model, or its banned list was not applied: {survivors}\n"
        f"--- transcript ---\n{result.text.strip()}"
    )
