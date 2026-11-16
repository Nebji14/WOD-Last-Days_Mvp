"""Modèles d'entrée et de sortie du chat général."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.accounts import Role
from app.domain.chat import MESSAGE_MAX_LENGTH, ChatMessage


class SendMessageRequest(BaseModel):
    """Envoi d'un message (US-013 · CA5).

    Attributs:
        client_token: jeton choisi par le client pour cet envoi ; le même jeton
            est renvoyé lors d'une nouvelle tentative après une coupure.
        body: texte du message, espaces de début et de fin retirés.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    client_token: UUID
    body: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)


class EditMessageRequest(BaseModel):
    """Nouveau texte d'un message (US-013 · CA6, US-030 · CA1)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    body: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)


class MessageAuthor(BaseModel):
    """Auteur d'un message, tel qu'il est affiché dans le chat."""

    id: UUID
    display_name: str
    role: Role


class MessageResponse(BaseModel):
    """Message tel qu'il est exposé au client.

    Attributs:
        body: ``None`` pour un message supprimé.
        edited: le message a été modifié (mention « (modifié) », US-030 · CA4).
        deleted_by: rôle de qui a supprimé le message, ``None`` s'il ne l'est pas.
    """

    id: UUID
    position: int
    author: MessageAuthor
    body: str | None
    sent_at: datetime
    edited: bool
    deleted_by: Literal["player", "gm"] | None

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
        )


class HistoryResponse(BaseModel):
    """Page d'historique, dans l'ordre chronologique."""

    messages: list[MessageResponse]
    has_more: bool
