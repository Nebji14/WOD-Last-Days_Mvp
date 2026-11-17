"""Cas d'usage des PNJ et de leurs catégories (US-039 à US-043, écrans 04c et 07).

Le droit d'accès (MJ uniquement) est contrôlé par les routes. La feuille d'un
PNJ se modifie par les mêmes services que celle d'un personnage joueur ; ce
service gère ce qui est propre au PNJ : liste, création, catégorie, notes
intégrées, Puissance / Finesse / Résilience et suppression.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.accounts import Account
from app.domain.character import Character
from app.domain.hierarchy import would_create_cycle
from app.domain.names import clean_name
from app.domain.npc_profile import NpcModel, NpcProfile
from app.domain.npcs import (
    CATEGORY_NAME_MAX,
    NpcCategory,
    NpcSummary,
    initial_sheet_values,
    initial_traits,
    validate_npc_field,
)
from app.domain.sheet_fields import FieldRule, FieldRuleError
from app.repositories.characters import NewCharacter
from app.services.character_access import (
    CharacterAccess,
    edit_conflict,
    not_found,
    rule_violation,
)
from app.services.characters import MAIN_FORM_NAME


class NpcStore(Protocol):
    """Accès aux PNJ et aux catégories attendu par le service."""

    async def list_categories(self) -> list[NpcCategory]: ...
    async def create_category(self, name: str, parent_id: UUID | None) -> UUID: ...
    async def rename_category(self, category_id: UUID, name: str) -> bool: ...
    async def move_category(self, category_id: UUID, parent_id: UUID | None) -> None: ...
    async def delete_category(self, category_id: UUID, parent_id: UUID | None) -> None: ...
    async def list_npcs(self) -> list[NpcSummary]: ...
    async def create_npc(
        self,
        model: NpcModel,
        category_id: UUID | None,
        traits: dict[str, int | None],
        new: NewCharacter,
    ) -> UUID: ...
    async def update_profile_field(
        self, character_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool: ...
    async def set_category(self, character_id: UUID, category_id: UUID | None) -> None: ...


class CharacterRemover(Protocol):
    """Suppression d'un personnage, PNJ compris, et de tout ce qui s'y rattache."""

    async def delete(self, character_id: UUID) -> None: ...


class NpcBroadcaster(Protocol):
    """Signal temps réel d'un changement de la liste des PNJ."""

    async def npcs_changed(self, recipients: set[UUID]) -> None: ...


@dataclass(frozen=True, slots=True)
class NpcDirectory:
    """Contenu de l'outil PNJ : catégories et cartes des PNJ (US-040 · CA1, CA4)."""

    categories: list[NpcCategory]
    npcs: list[NpcSummary]


def _invalid_name() -> AppError:
    return AppError(ErrorCode.VALIDATION_ERROR, "Nom vide ou trop long.", status_code=422)


class NpcService:
    """Cas d'usage des PNJ.

    Args:
        npcs: accès aux PNJ et aux catégories.
        characters: suppression des feuilles.
        access: lecture, droits et diffusion des personnages.
        broadcaster: signal temps réel de la liste.
    """

    def __init__(
        self,
        npcs: NpcStore,
        characters: CharacterRemover,
        access: CharacterAccess,
        broadcaster: NpcBroadcaster,
    ) -> None:
        self._npcs = npcs
        self._characters = characters
        self._access = access
        self._broadcaster = broadcaster

    async def directory(self) -> NpcDirectory:
        """Retourne les catégories et tous les PNJ."""
        return NpcDirectory(await self._npcs.list_categories(), await self._npcs.list_npcs())

    async def create(self, model: NpcModel, category_id: UUID | None) -> Character:
        """Crée une feuille de PNJ vierge, rangée dans la catégorie choisie (04c-I3, RM-021)."""
        await self._require_category(category_id)
        new = NewCharacter(initial_sheet_values(MAIN_FORM_NAME), [])
        character_id = await self._npcs.create_npc(model, category_id, initial_traits(model), new)
        await self._signal()
        return await self._access.changed(character_id)

    async def set_field(
        self, actor: Account, character_id: UUID, field: str, value: object, expected: object
    ) -> Character:
        """Modifie une donnée propre au PNJ : catégorie, notes, Puissance, Finesse, Résilience.

        Raises:
            AppError: ``not_found``, ``rule_violation`` (07-I2) ou ``edit_conflict``.
        """
        profile = await self._profile(actor, character_id)
        if field == "category_id":
            category_id = self._category_value(value)
            await self._require_category(category_id)
            await self._npcs.set_category(character_id, category_id)
        else:
            try:
                checked = validate_npc_field(profile, field, value)
                if type(expected) is not type(checked):
                    raise FieldRuleError(FieldRule.TYPE)
            except FieldRuleError as error:
                raise rule_violation(error.rule.value, field) from None
            assert isinstance(expected, str | int)  # noqa: S101 - garanti par le contrôle de type
            if not await self._npcs.update_profile_field(character_id, field, checked, expected):
                raise edit_conflict()
        await self._signal()
        return await self._access.changed(character_id)

    async def delete(self, actor: Account, character_id: UUID) -> None:
        """Supprime définitivement la feuille du PNJ (US-043)."""
        await self._profile(actor, character_id)
        await self._characters.delete(character_id)
        await self._access.notify(character_id, None, seat_affected=False)
        await self._signal()

    # --- Catégories (C07, 04c-I2) ------------------------------------------------------

    async def create_category(self, name: str, parent_id: UUID | None) -> UUID:
        """Crée une catégorie, à la racine ou sous la catégorie sélectionnée."""
        await self._require_category(parent_id)
        category_id = await self._npcs.create_category(self._name(name), parent_id)
        await self._signal()
        return category_id

    async def rename_category(self, category_id: UUID, name: str) -> None:
        if not await self._npcs.rename_category(category_id, self._name(name)):
            raise not_found()
        await self._signal()

    async def move_category(self, category_id: UUID, parent_id: UUID | None) -> None:
        """Range une catégorie sous une autre ; refusé s'il créerait un cycle (C07)."""
        parents = await self._parents()
        if category_id not in parents or (parent_id is not None and parent_id not in parents):
            raise not_found()
        if would_create_cycle(parents, category_id, parent_id):
            raise AppError(
                ErrorCode.FOLDER_CYCLE,
                "Une catégorie ne peut pas être rangée dans l'une de ses sous-catégories.",
                status_code=422,
            )
        await self._npcs.move_category(category_id, parent_id)
        await self._signal()

    async def delete_category(self, category_id: UUID) -> None:
        """Supprime une catégorie ; ses PNJ et sous-catégories remontent au parent (Q04c-2)."""
        parents = await self._parents()
        if category_id not in parents:
            raise not_found()
        await self._npcs.delete_category(category_id, parents[category_id])
        await self._signal()

    async def _signal(self) -> None:
        """Prévient le MJ, seul lecteur des PNJ, que la liste a changé."""
        await self._broadcaster.npcs_changed(await self._access.gm_recipients())

    async def _profile(self, actor: Account, character_id: UUID) -> NpcProfile:
        """Retourne le profil du PNJ modifiable ; un personnage joueur répond comme absent."""
        character = await self._access.editable(actor, character_id)
        if character.npc is None:
            raise not_found()
        return character.npc

    async def _parents(self) -> dict[UUID, UUID | None]:
        return {c.id: c.parent_id for c in await self._npcs.list_categories()}

    async def _require_category(self, category_id: UUID | None) -> None:
        if category_id is not None and category_id not in await self._parents():
            raise not_found()

    @staticmethod
    def _category_value(value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return UUID(str(value))
        except ValueError:
            raise rule_violation(FieldRule.TYPE.value, "category_id") from None

    @staticmethod
    def _name(name: str) -> str:
        cleaned = clean_name(name, CATEGORY_NAME_MAX)
        if cleaned is None:
            raise _invalid_name()
        return cleaned
