"""Règles métier du chat général.

Module pur : aucun accès réseau ni base de données.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.accounts import Account, Role

MESSAGE_MAX_LENGTH = 2000


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Message public du chat général.

    Attributs:
        position: rang d'envoi, croissant ; fixe l'ordre d'affichage.
        author_name: nom affiché du joueur (et non celui de son personnage).
        body: texte du message, ``None`` une fois le message supprimé.
        edited_at: date de la dernière modification, ``None`` si le message
            n'a jamais été modifié.
        deleted_by_role: rôle de qui a supprimé le message, ``None`` s'il ne
            l'est pas. Détermine la mention laissée à sa place.
        roll: détail d'un jet de dés publié dans le chat, ``None`` sinon.
    """

    id: UUID
    position: int
    author_id: UUID
    author_name: str
    author_role: Role
    body: str | None
    sent_at: datetime
    edited_at: datetime | None
    deleted_by_role: Role | None
    roll: dict[str, Any] | None = None

    @property
    def is_deleted(self) -> bool:
        """Un message supprimé ne garde que sa trace."""
        return self.deleted_by_role is not None


def can_edit_body(message: ChatMessage) -> bool:
    """Le texte d'un jet de dés est généré : il ne se modifie pas, il se supprime."""
    return message.roll is None


def can_moderate(actor: Account, message: ChatMessage) -> bool:
    """Indique si ``actor`` peut modifier ou supprimer ``message``.

    Un joueur n'agit que sur ses propres messages ; le MJ
    agit sur tous.
    """
    return actor.role is Role.GM or message.author_id == actor.id
