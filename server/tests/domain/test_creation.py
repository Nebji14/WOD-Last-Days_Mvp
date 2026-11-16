"""Règles de création : RM-001 (attributs), RM-002 (alerte), RM-003 (compétences), RM-004."""

from app.domain.creation import (
    CreationRule,
    Specialty,
    Violation,
    attribute_violations,
    attributes_to_discuss,
    skill_violations,
    specialty_violations,
)
from app.domain.traits import ATTRIBUTE_NAMES, SKILL_NAMES, Category

PRIORITIES = {Category.MENTAL: 1, Category.PHYSICAL: 2, Category.SOCIAL: 3}


def _attributes(**overrides: int) -> dict[str, int]:
    """Répartition valide : mental 5, physique 4, social 3 points ajoutés."""
    values = {
        "intelligence": 3, "wits": 3, "resolve": 2,
        "strength": 2, "dexterity": 3, "stamina": 2,
        "presence": 2, "manipulation": 2, "composure": 2,
    }  # fmt: skip
    return values | overrides


def _skills(**overrides: int) -> dict[str, int]:
    """Répartition valide : mental 11, physique 7, social 4 points."""
    values = dict.fromkeys(SKILL_NAMES, 0) | {
        "academics": 3, "investigation": 3, "occult": 3, "medicine": 2,
        "athletics": 2, "firearms": 3, "stealth": 2,
        "empathy": 2, "streetwise": 2,
    }  # fmt: skip
    return values | overrides


# --- RM-001 -----------------------------------------------------------------------------


def test_valid_attribute_allocation_has_no_violation() -> None:
    assert set(_attributes()) == set(ATTRIBUTE_NAMES)
    assert attribute_violations(PRIORITIES, _attributes()) == []


def test_unspent_or_overspent_attribute_budget_is_reported_per_category() -> None:
    assert attribute_violations(PRIORITIES, _attributes(resolve=1)) == [
        Violation(CreationRule.ATTRIBUTE_BUDGET, "mental")
    ]
    assert attribute_violations(PRIORITIES, _attributes(stamina=3)) == [
        Violation(CreationRule.ATTRIBUTE_BUDGET, "physical")
    ]


def test_budget_follows_the_chosen_priorities() -> None:
    swapped = {Category.MENTAL: 2, Category.PHYSICAL: 1, Category.SOCIAL: 3}

    assert attribute_violations(swapped, _attributes(resolve=1, stamina=3)) == []


def test_attribute_cannot_go_below_the_free_point_or_above_five() -> None:
    values = _attributes(intelligence=6, wits=1, resolve=1, presence=0, manipulation=3, composure=3)

    assert attribute_violations(PRIORITIES, values) == [
        Violation(CreationRule.ATTRIBUTE_RANGE, "intelligence"),
        Violation(CreationRule.ATTRIBUTE_RANGE, "presence"),
    ]


def test_priorities_must_rank_the_three_categories_differently() -> None:
    same = {Category.MENTAL: 1, Category.PHYSICAL: 1, Category.SOCIAL: 3}

    assert attribute_violations(same, _attributes()) == [
        Violation(CreationRule.PRIORITIES, "attributes")
    ]
    assert skill_violations({Category.MENTAL: 1}, _skills()) == [
        Violation(CreationRule.PRIORITIES, "skills")
    ]


# --- RM-002 -----------------------------------------------------------------------------


def test_attributes_at_four_or_five_are_flagged_without_blocking() -> None:
    values = _attributes(intelligence=4, wits=2)

    assert attribute_violations(PRIORITIES, values) == []
    assert attributes_to_discuss(values) == ["intelligence"]
    assert attributes_to_discuss(_attributes()) == []


# --- RM-003 -----------------------------------------------------------------------------


def test_valid_skill_allocation_has_no_violation() -> None:
    assert skill_violations(PRIORITIES, _skills()) == []


def test_skill_priorities_are_independent_from_attribute_priorities() -> None:
    reversed_order = {Category.MENTAL: 3, Category.PHYSICAL: 2, Category.SOCIAL: 1}
    values = dict.fromkeys(SKILL_NAMES, 0) | {
        "academics": 4,
        "athletics": 4, "brawl": 3,
        "empathy": 4, "persuasion": 4, "subterfuge": 3,
    }  # fmt: skip

    assert skill_violations(reversed_order, values) == []


def test_skill_budget_and_range_are_enforced() -> None:
    assert skill_violations(PRIORITIES, _skills(medicine=1)) == [
        Violation(CreationRule.SKILL_BUDGET, "mental")
    ]
    assert skill_violations(PRIORITIES, _skills(firearms=6, athletics=0, stealth=1)) == [
        Violation(CreationRule.SKILL_RANGE, "firearms")
    ]


# --- RM-004 -----------------------------------------------------------------------------


def _specialties() -> list[Specialty]:
    return [
        Specialty("firearms", "Fusil"),
        Specialty("occult", "Rituels"),
        Specialty("occult", "Démons"),
    ]


def test_three_specialties_on_trained_skills_are_valid() -> None:
    assert specialty_violations(_specialties(), _skills()) == []


def test_exactly_three_specialties_are_required() -> None:
    assert specialty_violations(_specialties()[:2], _skills()) == [
        Violation(CreationRule.SPECIALTY_COUNT)
    ]


def test_specialty_needs_a_skill_with_at_least_one_point() -> None:
    specialties = [*_specialties()[:2], Specialty("drive", "Poursuite")]

    assert specialty_violations(specialties, _skills()) == [
        Violation(CreationRule.SPECIALTY_SKILL, "drive")
    ]


def test_specialty_text_must_be_filled_short_and_without_comma() -> None:
    for label in ("  ", "x" * 101, "Fusil, Pistolet"):
        specialties = [*_specialties()[:2], Specialty("firearms", label)]

        assert specialty_violations(specialties, _skills()) == [
            Violation(CreationRule.SPECIALTY_TEXT, "firearms")
        ]
