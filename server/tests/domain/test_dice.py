"""Règles des jets : réserve, réussites, relances, dé de chance."""

import pytest

from app.domain.dice import (
    DiceRuleError,
    Outcome,
    PoolOptions,
    PoolPart,
    count_successes,
    outcome,
    pool_parts,
    pool_size,
    rerolls_after,
)
from app.domain.traits import ATTRIBUTE_NAMES, SKILL_NAMES
from app.domain.wounds import wound_penalty

TRAITS = dict.fromkeys(ATTRIBUTE_NAMES, 2) | dict.fromkeys(SKILL_NAMES, 0) | {"brawl": 2}


def _keys(parts: list[PoolPart]) -> list[tuple[str, int]]:
    return [(part.key, part.value) for part in parts]


# --- Réserve ----------------------------------------------------------------------------


def test_pool_adds_specialty_willpower_wounds_and_gm_modifier() -> None:
    options = PoolOptions(specialty=True, willpower=True, modifier=-2)

    parts = pool_parts(TRAITS, "strength", "brawl", True, options, wound_penalty=-1)

    assert _keys(parts) == [
        ("strength", 2),
        ("brawl", 2),
        ("specialty", 1),
        ("willpower", 3),
        ("wounds", -1),
        ("modifier", -2),
    ]
    assert pool_size(parts) == 5


@pytest.mark.parametrize(("skill", "penalty"), [("academics", -3), ("stealth", -1)])
def test_unskilled_penalty_depends_on_category(skill: str, penalty: int) -> None:
    parts = pool_parts(TRAITS, "wits", skill, False, PoolOptions(), 0)

    assert ("unskilled", penalty) in _keys(parts)


def test_two_attributes_make_a_pool_without_unskilled_penalty() -> None:
    parts = pool_parts(TRAITS, "resolve", "composure", False, PoolOptions(), 0)

    assert _keys(parts) == [("resolve", 2), ("composure", 2)]


def test_specialty_needs_a_skill_that_has_one() -> None:
    with pytest.raises(DiceRuleError):
        pool_parts(TRAITS, "strength", "brawl", False, PoolOptions(specialty=True), 0)


def test_empty_pool_gives_zero_dice() -> None:
    parts = pool_parts(TRAITS, "wits", "academics", False, PoolOptions(modifier=-5), 0)

    assert pool_size(parts) == 0


def test_wound_penalty_follows_the_last_three_boxes() -> None:
    assert [wound_penalty("/" * n, 7) for n in range(8)] == [0, 0, 0, 0, 0, -1, -2, -3]


# --- Réussites et relances --------------------------------------------------------------


def test_eight_and_more_succeed() -> None:
    assert count_successes([[1, 7, 8, 9, 10]], chance=False) == 3


def test_tens_are_rerolled_and_options_lower_the_threshold() -> None:
    faces = [10, 9, 8, 3]

    assert rerolls_after(faces, 10, rote_applies=False, chance=False) == 1
    assert rerolls_after(faces, 9, rote_applies=False, chance=False) == 2
    assert rerolls_after(faces, 8, rote_applies=False, chance=False) == 3


def test_rote_action_rerolls_failures_of_the_first_wave() -> None:
    assert rerolls_after([10, 3, 5, 8], 10, rote_applies=True, chance=False) == 3


def test_chance_die_succeeds_only_on_ten() -> None:
    assert count_successes([[9]], chance=True) == 0
    assert count_successes([[10]], chance=True) == 1
    assert rerolls_after([10], 8, rote_applies=True, chance=True) == 1


@pytest.mark.parametrize(
    ("stages", "chance", "expected"),
    [
        ([[1]], True, Outcome.DRAMATIC_FAILURE),
        ([[5]], True, Outcome.FAILURE),
        ([[3, 4]], False, Outcome.FAILURE),
        ([[8, 2]], False, Outcome.SUCCESS),
        ([[10, 9, 8, 8], [10], [9]], False, Outcome.EXCEPTIONAL),
    ],
)
def test_outcome(stages: list[list[int]], chance: bool, expected: Outcome) -> None:
    assert outcome(stages, chance) is expected
