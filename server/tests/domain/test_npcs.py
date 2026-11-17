"""Règles des PNJ : modèle, Puissance / Finesse / Résilience, champs du modèle simplifié."""

from uuid import uuid4

import pytest

from app.domain.npc_profile import NpcModel, NpcProfile
from app.domain.npcs import (
    check_npc_sheet_field,
    initial_sheet_values,
    initial_traits,
    validate_npc_field,
)
from app.domain.sheet_fields import FieldRule, FieldRuleError

SIMPLIFIED = NpcProfile(NpcModel.SIMPLIFIED, None, "", 1, 1, 1)
FULL = NpcProfile(NpcModel.FULL, uuid4(), "", None, None, None)


def test_simplified_traits_start_at_one_and_are_absent_for_full() -> None:
    assert initial_traits(NpcModel.SIMPLIFIED) == {"power": 1, "finesse": 1, "resilience": 1}
    assert initial_traits(NpcModel.FULL) == {"power": None, "finesse": None, "resilience": None}


def test_blank_sheet_starts_from_its_base_values() -> None:
    values = initial_sheet_values("Forme principale")

    assert values["name"] == "Nouveau PNJ"
    assert (values["size"], values["health_max"], values["willpower_max"]) == (5, 6, 2)
    assert values["willpower_current"] == values["willpower_max"]


@pytest.mark.parametrize(("value", "rule"), [(0, FieldRule.RANGE), (11, FieldRule.RANGE)])
def test_simplified_traits_are_bounded(value: int, rule: FieldRule) -> None:
    with pytest.raises(FieldRuleError) as refused:
        validate_npc_field(SIMPLIFIED, "power", value)
    assert refused.value.rule is rule


def test_simplified_traits_do_not_exist_on_a_full_npc() -> None:
    assert validate_npc_field(SIMPLIFIED, "finesse", 10) == 10
    with pytest.raises(FieldRuleError):
        validate_npc_field(FULL, "finesse", 3)


def test_notes_are_kept_as_typed() -> None:
    assert validate_npc_field(FULL, "notes", "  Secret : la marée.  ") == "  Secret : la marée.  "
    with pytest.raises(FieldRuleError):
        validate_npc_field(FULL, "notes", "x" * 20001)


def test_simplified_npc_refuses_attributes_and_skills() -> None:
    for field in ("strength", "firearms"):
        with pytest.raises(FieldRuleError):
            check_npc_sheet_field(SIMPLIFIED, field)
    check_npc_sheet_field(SIMPLIFIED, "health_max")
    check_npc_sheet_field(FULL, "strength")
    check_npc_sheet_field(None, "strength")
