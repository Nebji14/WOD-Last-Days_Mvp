"""Routes du chat général (US-013, US-029, US-030).

Toute route exige une session. Les droits sur un message (auteur ou MJ) sont
contrôlés par le service.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import ContainerDep, CurrentAccount, enforce_rate_limit
from app.schemas.chat import (
    EditMessageRequest,
    HistoryResponse,
    MessageResponse,
    SendMessageRequest,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

_HISTORY_PAGE_DEFAULT = 50
_HISTORY_PAGE_MAX = 100
_WRITE_WINDOW_SECONDS = 10.0
_WRITE_LIMIT_PER_ACCOUNT = 10


def _limit_writes(container: ContainerDep, account_id: UUID) -> None:
    """Limite le débit d'envoi, de modification et de suppression par compte."""
    enforce_rate_limit(
        container.rate_limiter,
        f"chat:account:{account_id}",
        _WRITE_LIMIT_PER_ACCOUNT,
        _WRITE_WINDOW_SECONDS,
    )


@router.get("/messages")
async def history(
    container: ContainerDep,
    _: CurrentAccount,
    before: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=_HISTORY_PAGE_MAX)] = _HISTORY_PAGE_DEFAULT,
) -> HistoryResponse:
    """Retourne une page d'historique, les plus récents par défaut (US-013 · CA1, CA2)."""
    messages, has_more = await container.chat_service.history(before, limit)
    return HistoryResponse(
        messages=[MessageResponse.from_message(message) for message in messages],
        has_more=has_more,
    )


@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: SendMessageRequest, container: ContainerDep, account: CurrentAccount
) -> MessageResponse:
    """Envoie un message dans le chat général (US-013 · CA5, US-029)."""
    _limit_writes(container, account.id)
    message = await container.chat_service.send(account, payload.client_token, payload.body)
    return MessageResponse.from_message(message)


@router.patch("/messages/{message_id}")
async def edit_message(
    message_id: UUID, payload: EditMessageRequest, container: ContainerDep, account: CurrentAccount
) -> MessageResponse:
    """Modifie un message : le sien, ou n'importe lequel pour le MJ (US-013 · CA6, US-030 · CA1)."""
    _limit_writes(container, account.id)
    message = await container.chat_service.edit(account, message_id, payload.body)
    return MessageResponse.from_message(message)


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: UUID, container: ContainerDep, account: CurrentAccount
) -> MessageResponse:
    """Supprime un message en laissant sa trace (US-013 · CA7, US-030 · CA2, CA5)."""
    _limit_writes(container, account.id)
    message = await container.chat_service.delete(account, message_id)
    return MessageResponse.from_message(message)
