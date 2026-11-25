"""Règles métier du chat général.

Module pur : aucun accès réseau ni base de données.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from app.domain.accounts import Account, Role

MESSAGE_MAX_LENGTH = 2000


class Notice(StrEnum):
    """Annonce publiée par le serveur : départ d'un joueur."""

    DISABLED = "account_disabled"
    DELETED = "account_deleted"


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Message public du chat général.

    Attributs:
        position: rang d'envoi, croissant ; fixe l'ordre d'affichage.
        author_id: auteur, ``None`` si son compte a été supprimé définitivement.
        author_name: nom affiché du joueur (et non celui de son personnage) ; vide
            sans auteur.
        body: texte du message, ``None`` une fois le message supprimé.
        edited_at: date de la dernière modification, ``None`` si le message
            n'a jamais été modifié.
        deleted_by_role: rôle de qui a supprimé le message, ``None`` s'il ne
            l'est pas. Détermine la mention laissée à sa place.
        roll: détail d'un jet de dés publié dans le chat, ``None`` sinon.
        notice: annonce du serveur, ``None`` pour un message ordinaire.
    """

    id: UUID
    position: int
    author_id: UUID | None
    author_name: str
    author_role: Role
    body: str | None
    sent_at: datetime
    edited_at: datetime | None
    deleted_by_role: Role | None
    roll: dict[str, Any] | None = None
    notice: Notice | None = None

    @property
    def is_deleted(self) -> bool:
        """Un message supprimé ne garde que sa trace."""
        return self.deleted_by_role is not None


def can_edit_body(message: ChatMessage) -> bool:
    """Un jet de dés ou une annonce est généré : il ne se modifie pas, il se supprime."""
    return message.roll is None and message.notice is None


def can_moderate(actor: Account, message: ChatMessage) -> bool:
    """Indique si ``actor`` peut modifier ou supprimer ``message``.

    Un joueur n'agit que sur ses propres messages, annonces exclues ; le MJ
    agit sur tous.
    """
    if actor.role is Role.GM:
        return True
    return message.notice is None and message.author_id == actor.id
