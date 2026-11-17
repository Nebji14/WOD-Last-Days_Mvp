"""Déclenchement de l'éveil d'un personnage par le MJ (04a-I5, notes 05 ÉVEIL).

L'éveil fait passer le plafond des attributs du personnage de 5 à 10. Il est
secret : un joueur qui appelle cette action reçoit la même réponse que pour un
personnage inexistant, sans indice sur la fonctionnalité. Il n'est pas
réversible au MVP (Q05-13) et le joueur n'est pas prévenu (Q05-14) : il le
découvre sur sa fiche, mise à jour en temps réel.
"""

from typing import Protocol
from uuid import UUID

from app.domain.accounts import Account, Role
from app.domain.character import Character
from app.services.character_access import CharacterAccess, not_found


class AwakeningStore(Protocol):
    """Écriture de l'éveil attendue par le service."""

    async def mark_awakened(self, character_id: UUID) -> None: ...


class AwakeningService:
    """Déclenche l'éveil et diffuse la fiche mise à jour.

    Args:
        store: enregistrement de la date d'éveil.
        access: droits, lecture et diffusion des personnages.
    """

    def __init__(self, store: AwakeningStore, access: CharacterAccess) -> None:
        self._store = store
        self._access = access

    async def awaken(self, actor: Account, character_id: UUID) -> Character:
        """Éveille le personnage ; sans effet s'il l'est déjà.

        Raises:
            AppError: ``not_found`` si l'acteur n'est pas le MJ ou si le
                personnage n'existe pas.
        """
        if actor.role is not Role.GM:
            raise not_found()
        character = await self._access.readable(actor, character_id)
        if character.is_awakened:
            return character
        await self._store.mark_awakened(character_id)
        return await self._access.changed(character_id)
