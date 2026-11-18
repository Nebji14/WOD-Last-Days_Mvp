"""Règles des ressources libres : nom, maximum, valeur disponible, nombre."""

from uuid import uuid4

import pytest

from app.domain.resources import (
    RESOURCES_MAX,
    Resource,
    ResourceRuleError,
    check_count,
    check_current,
    check_max,
    clean_name,
)

MANA = Resource(uuid4(), "Mana", 5, 3)


def test_name_is_trimmed() -> None:
    assert clean_name("  Douleur ", [MANA]) == "Douleur"


@pytest.mark.parametrize("name", ["", "   ", "x" * 41])
def test_name_must_be_filled_and_short(name: str) -> None:
    with pytest.raises(ResourceRuleError, match="resource_name"):
        clean_name(name, [])


def test_name_is_unique_whatever_the_case() -> None:
    with pytest.raises(ResourceRuleError, match="resource_name_taken"):
        clean_name("MANA", [MANA])


@pytest.mark.parametrize("value", [-1, 31])
def test_max_goes_from_0_to_30(value: int) -> None:
    check_max(0)
    check_max(30)
    with pytest.raises(ResourceRuleError):
        check_max(value)


@pytest.mark.parametrize("value", [-1, 6])
def test_current_stays_between_0_and_max(value: int) -> None:
    check_current(5, 5)
    with pytest.raises(ResourceRuleError, match="resource_above_max"):
        check_current(value, 5)


def test_a_character_holds_at_most_ten_resources() -> None:
    check_count(RESOURCES_MAX - 1)
    with pytest.raises(ResourceRuleError, match="resource_count"):
        check_count(RESOURCES_MAX)
