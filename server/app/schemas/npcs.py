"""Modèles d'entrée et de sortie de l'outil PNJ."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.npc_profile import NpcModel
from app.domain.npcs import CATEGORY_NAME_MAX, NpcCategory, NpcSummary
from app.services.npcs import NpcDirectory


class NpcCategoryResponse(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None

    @classmethod
    def from_category(cls, category: NpcCategory) -> "NpcCategoryResponse":
        return cls(id=category.id, name=category.name, parent_id=category.parent_id)


class NpcSummaryResponse(BaseModel):
    """PNJ de la liste : santé et volonté, plus Puissance, Finesse et Résilience en simplifié."""

    id: UUID
    name: str
    concept: str
    model: NpcModel
    category_id: UUID | None
    health_max: int
    willpower_max: int
    power: int | None
    finesse: int | None
    resilience: int | None

    @classmethod
    def from_summary(cls, npc: NpcSummary) -> "NpcSummaryResponse":
        return cls(
            id=npc.id,
            name=npc.name,
            concept=npc.concept,
            model=npc.profile.model,
            category_id=npc.profile.category_id,
            health_max=npc.health_max,
            willpower_max=npc.willpower_max,
            power=npc.profile.power,
            finesse=npc.profile.finesse,
            resilience=npc.profile.resilience,
        )


class NpcDirectoryResponse(BaseModel):
    categories: list[NpcCategoryResponse]
    npcs: list[NpcSummaryResponse]

    @classmethod
    def from_directory(cls, directory: NpcDirectory) -> "NpcDirectoryResponse":
        return cls(
            categories=[NpcCategoryResponse.from_category(c) for c in directory.categories],
            npcs=[NpcSummaryResponse.from_summary(n) for n in directory.npcs],
        )


class CreateNpcRequest(BaseModel):
    """Modèle choisi à la création et catégorie dans laquelle ranger le PNJ."""

    model: NpcModel
    category_id: UUID | None = None


class NpcFieldRequest(BaseModel):
    """Donnée propre au PNJ : ``category_id``, ``notes``, ``power``, ``finesse``, ``resilience``.

    La valeur est contrôlée par les règles du PNJ ; ``expected`` est
    la valeur affichée avant la saisie, inutile pour la catégorie.
    """

    field: str = Field(min_length=1, max_length=40)
    value: Any
    expected: Any = None


class CategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=CATEGORY_NAME_MAX)
    parent_id: UUID | None = None


class CategoryRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=CATEGORY_NAME_MAX)


class MoveCategoryRequest(BaseModel):
    parent_id: UUID | None


class CreatedResponse(BaseModel):
    id: UUID
