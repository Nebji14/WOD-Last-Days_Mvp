"""Modèles d'entrée des routes de personnages.

Ils bornent les types, les longueurs et les valeurs. Les règles métier qui
dépendent de l'état de la feuille sont appliquées par les services.
"""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, model_validator

from app.domain.character import EntryKind
from app.domain.creation import Specialty
from app.domain.traits import ATTRIBUTE_NAMES, SKILL_NAMES, Category
from app.domain.wounds import Wound
from app.repositories.sheet_items import EntryValues
from app.services.characters import CreationInput

_STRICT = ConfigDict(extra="forbid")
_STRIPPED = ConfigDict(extra="forbid", str_strip_whitespace=True)

Rank = Annotated[int, Field(ge=1, le=3)]
ShortText = Annotated[str, Field(max_length=120)]
LongText = Annotated[str, Field(max_length=4000)]


class IdentityInput(BaseModel):
    """Étape 1 de la création : le nom est obligatoire, le reste facultatif."""

    model_config = _STRIPPED

    name: str = Field(min_length=1, max_length=80)
    concept: ShortText = ""
    profession: ShortText = ""
    virtue: ShortText = ""
    vice: ShortText = ""
    compact: ShortText = ""


class SpecialtyInput(BaseModel):
    model_config = _STRIPPED

    skill: str = Field(max_length=40)
    label: str = Field(min_length=1, max_length=100)


class EffectiveInput(BaseModel):
    """Valeurs effectives retenues à l'étape 5 ; une valeur omise reprend la base."""

    model_config = _STRICT

    size: int | None = Field(default=None, ge=0, le=99)
    speed: int | None = Field(default=None, ge=0, le=99)
    defense: int | None = Field(default=None, ge=0, le=99)
    initiative: int | None = Field(default=None, ge=0, le=99)
    health_max: int | None = Field(default=None, ge=1, le=30)
    willpower_max: int | None = Field(default=None, ge=0, le=30)


class CreateCharacterRequest(BaseModel):
    """Saisie complète de l'assistant de création."""

    model_config = _STRICT

    identity: IdentityInput
    attribute_priorities: dict[Category, Rank]
    attributes: dict[str, Annotated[int, Field(ge=0, le=10)]]
    skill_priorities: dict[Category, Rank]
    skills: dict[str, Annotated[int, Field(ge=0, le=10)]]
    specialties: list[SpecialtyInput] = Field(max_length=10)
    effective: EffectiveInput = EffectiveInput()

    @model_validator(mode="after")
    def _complete_traits(self) -> Self:
        """Les neuf attributs et les vingt-quatre compétences sont tous fournis, sans autre clé."""
        if set(self.attributes) != set(ATTRIBUTE_NAMES) or set(self.skills) != set(SKILL_NAMES):
            raise ValueError("traits")
        return self

    def to_input(self) -> CreationInput:
        """Convertit la requête en saisie attendue par le service."""
        return CreationInput(
            identity=self.identity.model_dump(),
            attribute_priorities=self.attribute_priorities,
            attributes=self.attributes,
            skill_priorities=self.skill_priorities,
            skills=self.skills,
            specialties=[Specialty(s.skill, s.label) for s in self.specialties],
            effective=self.effective.model_dump(exclude_none=True),
        )


class FieldUpdateRequest(BaseModel):
    """Modification d'un seul champ, enregistré aussitôt.

    Attributs:
        expected: valeur affichée avant la saisie ; le serveur refuse l'écriture
            si elle a changé entre-temps.
    """

    model_config = _STRICT

    field: str = Field(min_length=1, max_length=40)
    value: StrictInt | StrictStr
    expected: StrictInt | StrictStr


class WoundRequest(BaseModel):
    """Action sur la piste de blessures."""

    model_config = _STRICT

    action: Literal["add", "heal", "worsen"]
    wound: Wound | None = None
    expected: str = Field(max_length=30)


class SpecialtiesRequest(BaseModel):
    """Champ de spécialités d'une compétence, valeurs séparées par des virgules."""

    model_config = _STRICT

    text: str = Field(max_length=400)


class FormRequest(BaseModel):
    model_config = _STRIPPED

    form_name: str = Field(min_length=1, max_length=60)


class MoralityNoteRequest(BaseModel):
    model_config = _STRIPPED

    level: int = Field(ge=1, le=10)
    body: str = Field(min_length=1, max_length=500)


class EntryValuesInput(BaseModel):
    """Valeurs d'un atout, handicap, pouvoir, objet, d'une arme ou d'une armure."""

    model_config = _STRICT

    name: ShortText = ""
    description: LongText = ""
    level: int | None = Field(default=None, ge=0, le=10)
    quantity: int | None = Field(default=None, ge=0, le=9999)
    damage_modifier: int | None = Field(default=None, ge=-20, le=20)
    range: str | None = Field(default=None, max_length=60)
    size: int | None = Field(default=None, ge=0, le=20)
    initiative_penalty: int | None = Field(default=None, ge=-20, le=20)
    general_protection: int | None = Field(default=None, ge=0, le=20)
    ballistic_protection: int | None = Field(default=None, ge=0, le=20)
    min_strength: int | None = Field(default=None, ge=0, le=10)
    defense_penalty: int | None = Field(default=None, ge=-20, le=20)

    def to_values(self) -> EntryValues:
        return EntryValues(**self.model_dump())


class CreateEntryRequest(EntryValuesInput):
    kind: EntryKind

    def to_values(self) -> EntryValues:
        return EntryValues(**self.model_dump(exclude={"kind"}))


class TacticRequest(BaseModel):
    """Rattache une tactique existante (``tactic_id``) ou en crée une nouvelle."""

    model_config = _STRICT

    tactic_id: UUID | None = None
    name: ShortText = ""
    description: LongText = ""


class TacticUpdateRequest(BaseModel):
    model_config = _STRICT

    name: ShortText = ""
    description: LongText = ""


class ExpenseRequest(BaseModel):
    """Dépense d'expérience : type, points et justification obligatoire."""

    model_config = _STRIPPED

    is_tactical: bool
    points: int = Field(ge=1, le=99999)
    justification: str = Field(min_length=1, max_length=500)


class ExpenseUpdateRequest(BaseModel):
    model_config = _STRIPPED

    points: int = Field(ge=1, le=99999)
    justification: str = Field(min_length=1, max_length=500)


class NoteUpdateRequest(BaseModel):
    model_config = _STRICT

    title: str = Field(max_length=120)
    body: str = Field(max_length=50000)
