"""Valeurs de base (RM-006, RM-007, RM-010) et découpage des spécialités (05-I9)."""

from app.domain.derived import base_values
from app.domain.traits import (
    ATTRIBUTE_NAMES,
    SKILL_NAMES,
    attribute_max,
    parse_specialties,
)


def _traits(**overrides: int) -> dict[str, int]:
    return dict.fromkeys(ATTRIBUTE_NAMES, 1) | dict.fromkeys(SKILL_NAMES, 0) | overrides


def test_base_values_follow_the_formulas() -> None:
    traits = _traits(
        strength=2, dexterity=3, wits=4, composure=2, resolve=3, stamina=2, athletics=2
    )

    base = base_values(traits, effective_size=5)

    assert base.size == 5
    assert base.speed == 2 + 3 + 5
    assert base.defense == min(4, 3) + 2
    assert base.initiative == 3 + 2
    assert base.health == 5 + 2
    assert base.willpower == 3 + 2


def test_defense_uses_the_lower_of_wits_and_dexterity() -> None:
    assert base_values(_traits(wits=1, dexterity=5), effective_size=5).defense == 1
    assert base_values(_traits(wits=5, dexterity=2), effective_size=5).defense == 2


def test_base_health_follows_the_effective_size() -> None:
    assert base_values(_traits(stamina=3), effective_size=6).health == 9


def test_attribute_cap_rises_with_the_awakening() -> None:
    assert attribute_max(awakened=False) == 5
    assert attribute_max(awakened=True) == 10


def test_there_are_nine_attributes_and_twenty_four_skills() -> None:
    assert len(ATTRIBUTE_NAMES) == len(set(ATTRIBUTE_NAMES)) == 9
    assert len(SKILL_NAMES) == len(set(SKILL_NAMES)) == 24


def test_specialties_are_split_on_commas_and_cleaned() -> None:
    assert parse_specialties("Fusil,  Pistolet ,, fusil,Arme   de poing") == [
        "Fusil",
        "Pistolet",
        "Arme de poing",
    ]
    assert parse_specialties("   ") == []
