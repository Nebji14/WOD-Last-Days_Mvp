"""Connexion temps réel de la table de jeu (WebSocket ``/ws``).

Déroulé :
  1. l'origine de la connexion est contrôlée avant toute acceptation ;
  2. le client envoie ``{"type": "auth", "ticket": "..."}`` comme premier
     message (voir ``app.realtime.tickets``) ;
  3. le serveur diffuse ensuite les événements de la table. Le client n'envoie
     rien d'autre : toute action passe par l'API HTTP, qui contrôle les droits.

La connexion est fermée à l'expiration de la session qui l'a ouverte ; le
client en ouvre une nouvelle après avoir renouvelé sa session.
"""

import asyncio
import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.deps import Container
from app.domain.accounts import Account
from app.domain.table import TableFullError
from app.realtime.hub import CLOSE_TABLE_FULL, CLOSE_UNAUTHENTICATED

logger = logging.getLogger(__name__)

router = APIRouter()

_CLOSE_POLICY_VIOLATION = 1008

_AUTH_TIMEOUT_SECONDS = 5.0
_MAX_CLIENT_MESSAGE_LENGTH = 512


@router.websocket("/ws")
async def table_socket(websocket: WebSocket) -> None:
    """Authentifie la connexion puis la maintient jusqu'à sa fermeture."""
    container: Container = websocket.app.state.container
    origin = (websocket.headers.get("origin") or "").rstrip("/")
    if origin not in container.settings.allowed_origins:
        await websocket.close(code=_CLOSE_POLICY_VIOLATION)
        return
    await websocket.accept()

    session = await _authenticate(websocket, container)
    if session is None:
        await websocket.close(code=CLOSE_UNAUTHENTICATED)
        return
    account, session_expires_at = session

    container.hub.add(account.id, websocket)
    try:
        await container.table_service.enter(account)
    except TableFullError:
        container.hub.remove(websocket)
        await websocket.close(code=CLOSE_TABLE_FULL)
        return
    try:
        await _hold_open(websocket, session_expires_at)
    finally:
        container.hub.remove(websocket)
        await container.table_service.leave(account)


async def _authenticate(websocket: WebSocket, container: Container) -> tuple[Account, float] | None:
    """Attend le ticket du client et retourne le compte et l'expiration de sa session.

    Returns:
        ``None`` si le premier message n'arrive pas à temps, s'il est mal formé,
        si le ticket est inconnu, déjà utilisé ou expiré, ou si le compte n'est
        plus actif.
    """
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), _AUTH_TIMEOUT_SECONDS)
    except (TimeoutError, WebSocketDisconnect, RuntimeError):
        return None
    ticket_value = _ticket_from(raw)
    if ticket_value is None:
        return None
    ticket = container.tickets.consume(ticket_value)
    if ticket is None:
        return None
    account = await container.auth_service.get_active_account(ticket.account_id)
    if account is None:
        return None
    return account, ticket.session_expires_at


def _ticket_from(raw: str) -> str | None:
    """Extrait le ticket du message d'authentification, ou ``None`` s'il est mal formé."""
    if len(raw) > _MAX_CLIENT_MESSAGE_LENGTH:
        return None
    try:
        message = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(message, dict) or message.get("type") != "auth":
        return None
    ticket = message.get("ticket")
    return ticket if isinstance(ticket, str) else None


async def _hold_open(websocket: WebSocket, session_expires_at: float) -> None:
    """Garde la connexion ouverte jusqu'au départ du client ou à l'expiration de la session.

    Les messages reçus après l'authentification sont ignorés ; un message
    anormalement long ferme la connexion.
    """
    while True:
        remaining = session_expires_at - time.time()
        if remaining <= 0:
            await websocket.close(code=CLOSE_UNAUTHENTICATED)
            return
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), remaining)
        except TimeoutError:
            continue
        except (WebSocketDisconnect, RuntimeError):
            return
        if len(raw) > _MAX_CLIENT_MESSAGE_LENGTH:
            await websocket.close(code=_CLOSE_POLICY_VIOLATION)
            return
