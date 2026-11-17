"""Modèles d'entrée et de sortie des jets de dés."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.accounts import Role
from app.domain.dice import (
    FREE_POOL_MAX,
    MODIFIER_MAX,
    MODIFIER_MIN,
    DiceRoll,
    RollKind,
    roll_detail,
)

_TRAIT_MAX_LENGTH = 32


class RollRequest(BaseModel):
    """Demande de jet.

    Attributs:
        attribute, second: attribut, puis compétence ou second attribut
            (jet ``pool``).
        trait: Puissance, Finesse ou Résilience (jet ``trait`` d'un PNJ simplifié).
        dice: nombre de dés d'un jet libre du MJ.
        secret: jet du MJ montré au MJ seul.
    """

    model_config = ConfigDict(extra="forbid")

    kind: RollKind
    character_id: UUID | None = None
    sheet_id: UUID | None = None
    attribute: str | None = Field(default=None, max_length=_TRAIT_MAX_LENGTH)
    second: str | None = Field(default=None, max_length=_TRAIT_MAX_LENGTH)
    trait: str | None = Field(default=None, max_length=_TRAIT_MAX_LENGTH)
    dice: int | None = Field(default=None, ge=1, le=FREE_POOL_MAX)
    specialty: bool = False
    willpower: bool = False
    modifier: int = Field(default=0, ge=MODIFIER_MIN, le=MODIFIER_MAX)
    again: int = Field(default=10, ge=8, le=10)
    rote: bool = False
    secret: bool = False


class RollPart(BaseModel):
    """Élément de la réserve."""

    key: str
    value: int


class RollResponse(BaseModel):
    """Jet tel qu'il est montré à la table et gardé dans le chat.

    Attributs:
        stages: faces de chaque vague ; la première est le lancer initial.
        pending: dés qui restent à relancer ; 0 quand le jet est terminé.
        outcome: issue du jet de réussites, ``None`` tant qu'il n'est pas terminé
            ou pour l'initiative.
        total: résultat d'un jet d'initiative.
    """

    id: UUID
    roller_id: UUID
    roller_role: Role
    roller_name: str
    character_id: UUID | None
    kind: RollKind
    parts: list[RollPart]
    chance: bool
    again: int
    rote: bool
    secret: bool
    stages: list[list[int]]
    pending: int
    successes: int
    outcome: str | None
    total: int | None

    @classmethod
    def from_roll(cls, roll: DiceRoll) -> "RollResponse":
        """Projette un jet du domaine."""
        return cls.model_validate(roll_detail(roll))
