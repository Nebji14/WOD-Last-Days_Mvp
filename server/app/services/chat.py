"""Cas d'usage du chat général : historique, envoi, modification, suppression.

Couvre US-013 (joueur), US-029 (MJ) et US-030 (modération par le MJ).
"""

from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.accounts import Account
from app.domain.chat import ChatMessage, can_moderate


class MessageStore(Protocol):
    """Contrat d'accès aux messages attendu par le service."""

    async def get(self, message_id: UUID) -> ChatMessage | None: ...

    async def list_page(self, before: int | None, limit: int) -> list[ChatMessage]: ...

    async def create(self, author_id: UUID, client_token: UUID, body: str) -> ChatMessage: ...

    async def update_body(self, message_id: UUID, body: str) -> ChatMessage | None: ...

    async def mark_deleted(self, message_id: UUID, deleted_by: UUID) -> ChatMessage | None: ...


class ChatBroadcaster(Protocol):
    """Diffusion en temps réel d'un message créé, modifié ou supprimé."""

    async def message_changed(self, message: ChatMessage) -> None: ...


def _not_found() -> AppError:
    return AppError(ErrorCode.NOT_FOUND, "Message introuvable.", status_code=404)


class ChatService:
    """Orchestre le dépôt des messages et leur diffusion à la table.

    Args:
        messages: dépôt des messages.
        broadcaster: diffusion en temps réel vers les participants connectés.
    """

    def __init__(self, messages: MessageStore, broadcaster: ChatBroadcaster) -> None:
        self._messages = messages
        self._broadcaster = broadcaster

    async def history(self, before: int | None, limit: int) -> tuple[list[ChatMessage], bool]:
        """Retourne une page d'historique (US-013 · CA1, CA2).

        Args:
            before: position en deçà de laquelle chercher ; ``None`` pour la
                page la plus récente.
            limit: taille de la page.

        Returns:
            Les messages dans l'ordre chronologique, et un indicateur signalant
            qu'il en existe de plus anciens.
        """
        page = await self._messages.list_page(before, limit + 1)
        has_more = len(page) > limit
        return list(reversed(page[:limit])), has_more

    async def send(self, author: Account, client_token: UUID, body: str) -> ChatMessage:
        """Envoie un message et le diffuse (US-013 · CA3, CA5 ; US-029).

        Un envoi rejoué avec le même ``client_token`` retourne le message déjà
        enregistré (CDC 12.3 : nouvelle tentative sans doublon).
        """
        message = await self._messages.create(author.id, client_token, body)
        await self._broadcaster.message_changed(message)
        return message

    async def edit(self, actor: Account, message_id: UUID, body: str) -> ChatMessage:
        """Modifie un message et diffuse le changement (US-013 · CA6, US-030 · CA1, CA3, CA4).

        Raises:
            AppError: ``not_found`` si le message n'existe pas, ``forbidden`` si
                ``actor`` n'a pas le droit d'y toucher, ``message_deleted`` s'il
                a été supprimé.
        """
        await self._require_moderable(actor, message_id)
        message = await self._messages.update_body(message_id, body)
        if message is None:
            raise AppError(ErrorCode.MESSAGE_DELETED, "Ce message a été supprimé.", status_code=409)
        await self._broadcaster.message_changed(message)
        return message

    async def delete(self, actor: Account, message_id: UUID) -> ChatMessage:
        """Supprime un message en laissant sa trace (US-013 · CA7, US-030 · CA2, CA3, CA5).

        Supprimer un message déjà supprimé ne change rien et n'échoue pas.

        Raises:
            AppError: ``not_found`` ou ``forbidden``, comme pour ``edit``.
        """
        current = await self._require_moderable(actor, message_id)
        message = await self._messages.mark_deleted(message_id, actor.id)
        if message is None:
            return await self._messages.get(message_id) or current
        await self._broadcaster.message_changed(message)
        return message

    async def _require_moderable(self, actor: Account, message_id: UUID) -> ChatMessage:
        """Retourne le message si ``actor`` peut le modifier ou le supprimer."""
        message = await self._messages.get(message_id)
        if message is None:
            raise _not_found()
        if not can_moderate(actor, message):
            raise AppError(
                ErrorCode.FORBIDDEN,
                "Tu ne peux agir que sur tes propres messages.",
                status_code=403,
            )
        return message
