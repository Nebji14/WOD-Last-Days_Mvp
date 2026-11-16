"""Règles métier du chat général (US-013, US-029, US-030).

Module pur : aucun accès réseau ni base de données.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.accounts import Account, Role

MESSAGE_MAX_LENGTH = 2000


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Message public du chat général.

    Attributs:
        position: rang d'envoi, croissant ; fixe l'ordre d'affichage.
        author_name: nom affiché de l'auteur (Q03-6 : nom du joueur).
        body: texte du message, ``None`` une fois le message supprimé.
        edited_at: date de la dernière modification, ``None`` si le message
            n'a jamais été modifié (US-030 · CA4).
        deleted_by_role: rôle de qui a supprimé le message, ``None`` s'il ne
            l'est pas. Détermine la mention laissée à sa place (US-030 · CA5).
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

    @property
    def is_deleted(self) -> bool:
        """Un message supprimé ne garde que sa trace."""
        return self.deleted_by_role is not None


def can_moderate(actor: Account, message: ChatMessage) -> bool:
    """Indique si ``actor`` peut modifier ou supprimer ``message``.

    Un joueur n'agit que sur ses propres messages (US-013 · CA6 à CA8) ; le MJ
    agit sur tous (US-030 · CA1, CA2).
    """
    return actor.role is Role.GM or message.author_id == actor.id
