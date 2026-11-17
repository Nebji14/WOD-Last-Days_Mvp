"""Doublure du dépôt des PNJ, construite sur les personnages en mémoire."""

from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

from app.domain.npc_profile import NpcModel, NpcProfile
from app.domain.npcs import NpcCategory, NpcSummary
from app.repositories.characters import NewCharacter
from tests.fake_characters import FakeCharacterStore


class FakeNpcStore:
    """Catégories en mémoire ; les PNJ sont des personnages de ``FakeCharacterStore``."""

    def __init__(self, characters: FakeCharacterStore) -> None:
        self._characters = characters
        self.categories: dict[UUID, NpcCategory] = {}

    async def list_categories(self) -> list[NpcCategory]:
        return sorted(self.categories.values(), key=lambda c: c.name.lower())

    async def create_category(self, name: str, parent_id: UUID | None) -> UUID:
        category = NpcCategory(uuid4(), name, parent_id)
        self.categories[category.id] = category
        return category.id

    async def rename_category(self, category_id: UUID, name: str) -> bool:
        if category_id not in self.categories:
            return False
        self.categories[category_id] = replace(self.categories[category_id], name=name)
        return True

    async def move_category(self, category_id: UUID, parent_id: UUID | None) -> None:
        self.categories[category_id] = replace(self.categories[category_id], parent_id=parent_id)

    async def delete_category(self, category_id: UUID, parent_id: UUID | None) -> None:
        for npc in self._characters.npcs():
            assert npc.npc is not None
            if npc.npc.category_id == category_id:
                await self.set_category(npc.id, parent_id)
        for category in list(self.categories.values()):
            if category.parent_id == category_id:
                self.categories[category.id] = replace(category, parent_id=parent_id)
        del self.categories[category_id]

    async def list_npcs(self) -> list[NpcSummary]:
        summaries = []
        for npc in self._characters.npcs():
            assert npc.npc is not None
            main = npc.main_sheet
            summaries.append(
                NpcSummary(
                    id=npc.id,
                    name=main.texts["name"],
                    concept=main.texts["concept"],
                    profile=npc.npc,
                    health_max=main.numbers["health_max"],
                    willpower_max=main.numbers["willpower_max"],
                )
            )
        return sorted(summaries, key=lambda s: s.name.lower())

    async def create_npc(
        self,
        model: NpcModel,
        category_id: UUID | None,
        traits: dict[str, int | None],
        new: NewCharacter,
    ) -> UUID:
        profile = NpcProfile(
            model, category_id, "", traits["power"], traits["finesse"], traits["resilience"]
        )
        return self._characters.add_npc(new, profile)

    async def update_profile_field(
        self, character_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool:
        profile = self._profile(character_id)
        if getattr(profile, field) != expected:
            return False
        changes: dict[str, Any] = {field: value}
        self._characters.set_npc(character_id, replace(profile, **changes))
        return True

    async def set_category(self, character_id: UUID, category_id: UUID | None) -> None:
        profile = self._profile(character_id)
        self._characters.set_npc(character_id, replace(profile, category_id=category_id))

    def _profile(self, character_id: UUID) -> NpcProfile:
        npc = next(c for c in self._characters.npcs() if c.id == character_id)
        assert npc.npc is not None
        return npc.npc
