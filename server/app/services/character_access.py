"""Socle commun des cas d'usage sur les personnages : droits, lecture, diffusion.

Tout cas d'usage suit le même déroulé : charger le personnage, vérifier le droit
de l'acteur (CDC 8.3), appliquer le changement, puis relire le personnage et
prévenir en temps réel ceux qui peuvent le voir.
"""

from collections.abc import Awaitable, Callable
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.accounts import Account
from app.domain.character import Character, Sheet, can_edit, can_read


class CharacterReader(Protocol):
    """Lecture d'un personnage complet."""

    async def get(self, character_id: UUID) -> Character | None: ...


class GmDirectory(Protocol):
    """Accès au compte du MJ."""

    async def get_gm(self) -> Account | None: ...


class CharacterBroadcaster(Protocol):
    """Diffusion en temps réel d'un changement de personnage.

    L'événement ne porte que l'identifiant : chaque destinataire relit la fiche
    par l'API, qui applique ses droits et masque ce qu'il ne doit pas voir.
    """

    async def character_changed(self, character_id: UUID, recipients: set[UUID]) -> None: ...


def not_found() -> AppError:
    """Erreur unique pour un personnage absent ou inaccessible à l'acteur."""
    return AppError(ErrorCode.NOT_FOUND, "Personnage introuvable.", status_code=404)


def rule_violation(rule: str, subject: str | None = None) -> AppError:
    """Refus d'une saisie contraire à une règle métier (US-009 · CA3, 05-E2)."""
    detail = {"rule": rule} | ({"field": subject} if subject else {})
    return AppError(
        ErrorCode.RULE_VIOLATION,
        "Cette valeur ne respecte pas les règles de la feuille.",
        status_code=422,
        details=[detail],
    )


def edit_conflict() -> AppError:
    """La valeur a changé entre-temps : rien n'est écrasé (CDC 12.3, 05-E3)."""
    return AppError(
        ErrorCode.EDIT_CONFLICT,
        "Cette valeur vient d'être modifiée par quelqu'un d'autre.",
        status_code=409,
    )


class CharacterAccess:
    """Droits d'accès, lecture et diffusion, partagés par les services de personnages.

    Args:
        characters: lecture des personnages.
        accounts: accès au compte du MJ, destinataire de tous les changements.
        broadcaster: diffusion en temps réel.
        refresh_table: rediffuse l'état de la table quand un personnage joué change.
    """

    def __init__(
        self,
        characters: CharacterReader,
        accounts: GmDirectory,
        broadcaster: CharacterBroadcaster,
        refresh_table: Callable[[], Awaitable[None]],
    ) -> None:
        self._reader = characters
        self._accounts = accounts
        self._broadcaster = broadcaster
        self._refresh_table = refresh_table
        self._gm_id: UUID | None = None

    async def readable(self, actor: Account, character_id: UUID) -> Character:
        """Retourne le personnage si ``actor`` peut le consulter (US-008, US-026).

        Raises:
            AppError: ``not_found`` s'il n'existe pas ou n'est pas accessible.
        """
        character = await self._reader.get(character_id)
        if character is None or not can_read(actor, character.owner_id):
            raise not_found()
        return character

    async def editable(self, actor: Account, character_id: UUID | None) -> Character:
        """Retourne le personnage si ``actor`` peut le modifier (US-009, US-027).

        Raises:
            AppError: ``not_found`` s'il n'existe pas ou n'est pas accessible.
        """
        if character_id is None:
            raise not_found()
        character = await self.readable(actor, character_id)
        if not can_edit(actor, character.owner_id):
            raise not_found()
        return character

    @staticmethod
    def sheet_of(character: Character, sheet_id: UUID) -> Sheet:
        """Retourne la forme demandée du personnage.

        Raises:
            AppError: ``not_found`` si elle n'appartient pas à ce personnage.
        """
        sheet = character.sheet(sheet_id)
        if sheet is None:
            raise not_found()
        return sheet

    async def changed(self, character_id: UUID) -> Character:
        """Relit le personnage après un changement et prévient son propriétaire et le MJ.

        Raises:
            AppError: ``not_found`` si le personnage a été supprimé entre-temps.
        """
        character = await self._reader.get(character_id)
        if character is None:
            raise not_found()
        await self.notify(character.id, character.owner_id, character.is_played)
        return character

    async def notify(self, character_id: UUID, owner_id: UUID, seat_affected: bool) -> None:
        """Diffuse le changement, et l'état de la table si un siège l'affiche (US-009 · CA1)."""
        recipients = {owner_id}
        if self._gm_id is None:
            gm = await self._accounts.get_gm()
            self._gm_id = gm.id if gm else None
        if self._gm_id is not None:
            recipients.add(self._gm_id)
        await self._broadcaster.character_changed(character_id, recipients)
        if seat_affected:
            await self._refresh_table()
