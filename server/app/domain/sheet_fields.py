"""Champs modifiables d'une feuille et contrôle de leurs valeurs.

Chaque champ est enregistré seul, dès sa saisie. Ce module dit quels champs
existent, leur type, leurs bornes, et les règles métier qui lient un champ aux
autres valeurs de la feuille.

Les noms de champs servent aussi de noms de colonnes : la liste fermée de ce
module est la seule source acceptée par le dépôt.

Module pur : aucun accès réseau ni base de données.
"""

from enum import StrEnum

from app.domain.character import Sheet
from app.domain.traits import (
    ATTRIBUTE_MIN,
    ATTRIBUTE_NAMES,
    SKILL_MAX,
    SKILL_MIN,
    SKILL_NAMES,
    attribute_max,
)

# Longueur maximale de chaque champ de texte.
TEXT_FIELDS: dict[str, int] = {
    "form_name": 60,
    "name": 80,
    "concept": 120,
    "profession": 120,
    "virtue": 120,
    "vice": 120,
    "compact": 120,
    "age": 60,
    "height": 60,
    "weight": 60,
    "sex": 60,
    "hair": 60,
    "eyes": 60,
    "origin": 120,
    "nationality": 120,
    "history": 20000,
    "description": 20000,
    "global_protection": 60,
}
# Champs de texte qui ne peuvent pas être vides.
REQUIRED_TEXT_FIELDS = frozenset({"form_name", "name"})

# Bornes des valeurs effectives saisies et des jauges.
NUMBER_FIELDS: dict[str, tuple[int, int]] = {
    "size": (0, 99),
    "speed": (0, 99),
    "defense": (0, 99),
    "initiative": (0, 99),
    "health_max": (1, 30),
    "willpower_max": (0, 30),
    "willpower_current": (0, 30),
    "morality": (1, 10),
}

SHEET_FIELDS = frozenset({*TEXT_FIELDS, *NUMBER_FIELDS, *ATTRIBUTE_NAMES, *SKILL_NAMES})


class FieldRule(StrEnum):
    """Règle qui refuse une valeur."""

    UNKNOWN_FIELD = "unknown_field"
    TYPE = "type"
    REQUIRED = "required"
    LENGTH = "length"
    RANGE = "range"
    # Pas plus de blessures que de cases de santé.
    HEALTH_BELOW_WOUNDS = "health_below_wounds"
    # La volonté disponible reste entre zéro et la volonté maximale.
    WILLPOWER_ABOVE_MAX = "willpower_above_max"


class FieldRuleError(Exception):
    """La valeur proposée pour un champ est refusée.

    Attributs:
        rule: règle en cause, transmise au client pour qu'il l'explique.
    """

    def __init__(self, rule: FieldRule) -> None:
        super().__init__(rule.value)
        self.rule = rule


def _check_range(value: int, low: int, high: int) -> None:
    if not low <= value <= high:
        raise FieldRuleError(FieldRule.RANGE)


def validate_field(sheet: Sheet, field: str, value: object, awakened: bool) -> str | int:
    """Contrôle la nouvelle valeur d'un champ et la retourne normalisée.

    Args:
        sheet: feuille dans son état actuel.
        field: nom du champ.
        value: valeur proposée.
        awakened: le personnage est éveillé ; le plafond des attributs passe
            alors de 5 à 10. Avant l'éveil, le dépassement est refusé comme
            toute valeur hors bornes, sans autre indication.

    Raises:
        FieldRuleError: si le champ est inconnu ou la valeur refusée.
    """
    if field in TEXT_FIELDS:
        if not isinstance(value, str):
            raise FieldRuleError(FieldRule.TYPE)
        text = value.strip()
        if not text and field in REQUIRED_TEXT_FIELDS:
            raise FieldRuleError(FieldRule.REQUIRED)
        if len(text) > TEXT_FIELDS[field]:
            raise FieldRuleError(FieldRule.LENGTH)
        return text

    if field not in SHEET_FIELDS:
        raise FieldRuleError(FieldRule.UNKNOWN_FIELD)
    if isinstance(value, bool) or not isinstance(value, int):
        raise FieldRuleError(FieldRule.TYPE)

    if field in ATTRIBUTE_NAMES:
        _check_range(value, ATTRIBUTE_MIN, attribute_max(awakened))
    elif field in SKILL_NAMES:
        _check_range(value, SKILL_MIN, SKILL_MAX)
    else:
        _check_range(value, *NUMBER_FIELDS[field])
        if field == "health_max" and value < len(sheet.wound_track):
            raise FieldRuleError(FieldRule.HEALTH_BELOW_WOUNDS)
        if field == "willpower_max" and value < sheet.numbers["willpower_current"]:
            raise FieldRuleError(FieldRule.WILLPOWER_ABOVE_MAX)
        if field == "willpower_current" and value > sheet.numbers["willpower_max"]:
            raise FieldRuleError(FieldRule.WILLPOWER_ABOVE_MAX)
    return value


def current_value(sheet: Sheet, field: str) -> str | int:
    """Valeur actuelle d'un champ de la feuille.

    Raises:
        FieldRuleError: si le champ est inconnu.
    """
    if field == "form_name":
        return sheet.form_name
    if field in TEXT_FIELDS:
        return sheet.texts[field]
    if field in NUMBER_FIELDS:
        return sheet.numbers[field]
    if field in sheet.traits:
        return sheet.traits[field]
    raise FieldRuleError(FieldRule.UNKNOWN_FIELD)
