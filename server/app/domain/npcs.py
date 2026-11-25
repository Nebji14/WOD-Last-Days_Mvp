"""Règles pures des feuilles de PNJ.

Aucun accès réseau ni base.
"""

from dataclasses import dataclass
from uuid import UUID

from app.domain.derived import BASE_SIZE, base_values
from app.domain.npc_profile import NpcModel, NpcProfile
from app.domain.sheet_fields import FieldRule, FieldRuleError
from app.domain.traits import ATTRIBUTE_MIN, ATTRIBUTE_NAMES, SKILL_MIN, SKILL_NAMES

NPC_NOTES_MAX = 20000
CATEGORY_NAME_MAX = 60
SIMPLIFIED_TRAIT_MIN = 1
SIMPLIFIED_TRAIT_MAX = 10
DEFAULT_NPC_NAME = "Nouveau PNJ"
SIMPLIFIED_TRAITS = ("power", "finesse", "resilience")
"""Puissance, Finesse, Résilience."""


@dataclass(frozen=True, slots=True)
class NpcCategory:
    """Catégorie de PNJ : parent facultatif, sans cycle."""

    id: UUID
    name: str
    parent_id: UUID | None


@dataclass(frozen=True, slots=True)
class NpcSummary:
    """PNJ tel qu'il apparaît dans la liste : nom, modèle, concept et résumé chiffré."""

    id: UUID
    sheet_id: UUID
    name: str
    concept: str
    profile: NpcProfile
    health_max: int
    willpower_max: int
    portrait: str | None = None


def check_npc_sheet_field(profile: NpcProfile | None, field: str) -> None:
    """Refuse les attributs et compétences d'un PNJ simplifié, non renseignés.

    Raises:
        FieldRuleError: ``unknown_field`` pour ces champs sur un PNJ simplifié.
    """
    if profile is not None and profile.is_simplified and field in (*ATTRIBUTE_NAMES, *SKILL_NAMES):
        raise FieldRuleError(FieldRule.UNKNOWN_FIELD)


def initial_sheet_values(form_name: str) -> dict[str, str | int]:
    """Feuille vierge d'un PNJ : attributs et compétences au minimum.

    Les valeurs effectives partent des valeurs de base de cette feuille ; le
    MJ les fixe ensuite librement, santé et volonté comprises.
    """
    traits = dict.fromkeys(ATTRIBUTE_NAMES, ATTRIBUTE_MIN) | dict.fromkeys(SKILL_NAMES, SKILL_MIN)
    base = base_values(traits, BASE_SIZE)
    return {
        "form_name": form_name,
        "name": DEFAULT_NPC_NAME,
        "size": base.size,
        "speed": base.speed,
        "defense": base.defense,
        "initiative": base.initiative,
        "health_max": base.health,
        "willpower_max": base.willpower,
        "willpower_current": base.willpower,
    }


def initial_traits(model: NpcModel) -> dict[str, int | None]:
    """Puissance, Finesse et Résilience à la création : 1 en simplifié, absentes en complet."""
    value = SIMPLIFIED_TRAIT_MIN if model is NpcModel.SIMPLIFIED else None
    return dict.fromkeys(SIMPLIFIED_TRAITS, value)


def validate_npc_field(profile: NpcProfile, field: str, value: object) -> str | int:
    """Contrôle la saisie d'une donnée propre au PNJ.

    Args:
        profile: données actuelles du PNJ.
        field: ``notes``, ``power``, ``finesse`` ou ``resilience``.
        value: valeur saisie.

    Returns:
        La valeur à enregistrer (texte tel quel, ou entier).

    Raises:
        FieldRuleError: champ inconnu ou réservé au modèle simplifié, type ou
            bornes non respectés.
    """
    if field == "notes":
        if not isinstance(value, str):
            raise FieldRuleError(FieldRule.TYPE)
        if len(value) > NPC_NOTES_MAX:
            raise FieldRuleError(FieldRule.LENGTH)
        return value
    if field not in SIMPLIFIED_TRAITS or not profile.is_simplified:
        raise FieldRuleError(FieldRule.UNKNOWN_FIELD)
    if not isinstance(value, int) or isinstance(value, bool):
        raise FieldRuleError(FieldRule.TYPE)
    if not SIMPLIFIED_TRAIT_MIN <= value <= SIMPLIFIED_TRAIT_MAX:
        raise FieldRuleError(FieldRule.RANGE)
    return value
