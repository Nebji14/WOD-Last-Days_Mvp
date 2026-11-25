"""Modèles d'entrée et de sortie du chat général."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.accounts import Role
from app.domain.chat import MESSAGE_MAX_LENGTH, ChatMessage, Notice


class SendMessageRequest(BaseModel):
    """Envoi d'un message.

    Attributs:
        client_token: jeton choisi par le client pour cet envoi ; le même jeton
            est renvoyé lors d'une nouvelle tentative après une coupure.
        body: texte du message, espaces de début et de fin retirés.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    client_token: UUID
    body: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)


class EditMessageRequest(BaseModel):
    """Nouveau texte d'un message."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    body: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)


class MessageAuthor(BaseModel):
    """Auteur d'un message ; sans identifiant ni nom si son compte a été supprimé."""

    id: UUID | None
    display_name: str
    role: Role


class MessageResponse(BaseModel):
    """Message tel qu'il est exposé au client.

    Attributs:
        body: ``None`` pour un message supprimé.
        edited: le message a été modifié (mention « (modifié) » visible par tous).
        deleted_by: rôle de qui a supprimé le message, ``None`` s'il ne l'est pas.
        roll: détail d'un jet de dés, ``None`` pour un message ordinaire ou supprimé.
        notice: annonce du départ d'un joueur, ``None`` pour un message ordinaire.
    """

    id: UUID
    position: int
    author: MessageAuthor
    body: str | None
    sent_at: datetime
    edited: bool
    deleted_by: Literal["player", "gm"] | None
    roll: dict[str, Any] | None = None
    notice: Notice | None = None

    @classmethod
    def from_message(cls, message: ChatMessage) -> "MessageResponse":
        """Projette un message du domaine vers sa représentation publique."""
        return cls(
            id=message.id,
            position=message.position,
            author=MessageAuthor(
                id=message.author_id,
                display_name=message.author_name,
                role=message.author_role,
            ),
            body=message.body,
            sent_at=message.sent_at,
            edited=message.edited_at is not None and not message.is_deleted,
            deleted_by=message.deleted_by_role.value if message.deleted_by_role else None,
            roll=None if message.is_deleted else message.roll,
            notice=message.notice,
        )


class HistoryResponse(BaseModel):
    """Page d'historique, dans l'ordre chronologique."""

    messages: list[MessageResponse]
    has_more: bool
