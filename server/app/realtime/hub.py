"""Registre des connexions temps réel et diffusion des événements.

Chaque événement est un objet JSON ``{"type": ..., "data": ...}``. L'état de
la table et le chat partent vers toutes les connexions authentifiées ; un
changement de personnage ne part que vers ceux qui peuvent consulter sa fiche.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from fastapi import WebSocket

from app.domain.chat import ChatMessage
from app.schemas.chat import MessageResponse
from app.schemas.table import TableStateResponse
from app.services.table import TableState

logger = logging.getLogger(__name__)

EVENT_TABLE_STATE = "table.state"
EVENT_CHAT_MESSAGE = "chat.message"
EVENT_CHARACTER_CHANGED = "character.changed"
EVENT_IMAGES_CHANGED = "images.changed"

# Codes de fermeture applicatifs (plage 4000-4999 réservée aux applications).
CLOSE_UNAUTHENTICATED = 4401
CLOSE_TABLE_FULL = 4409

_SEND_TIMEOUT_SECONDS = 5.0


class ConnectionHub:
    """Connexions WebSocket authentifiées, regroupées par compte.

    Implémente les contrats de diffusion attendus par les services
    (``TableBroadcaster``, ``ChatBroadcaster``, ``CharacterBroadcaster``).
    """

    def __init__(self) -> None:
        self._connections: dict[WebSocket, UUID] = {}

    def add(self, account_id: UUID, websocket: WebSocket) -> None:
        """Enregistre une connexion authentifiée."""
        self._connections[websocket] = account_id

    def remove(self, websocket: WebSocket) -> None:
        """Oublie une connexion. Sans effet si elle n'est pas enregistrée."""
        self._connections.pop(websocket, None)

    async def table_changed(self, state: TableState) -> None:
        """Diffuse l'état de présence de la table (03-A6, 03-E2)."""
        await self._broadcast(
            EVENT_TABLE_STATE, TableStateResponse.from_state(state).model_dump(mode="json")
        )

    async def message_changed(self, message: ChatMessage) -> None:
        """Diffuse un message créé, modifié ou supprimé (US-013 · CA3, US-030 · CA3)."""
        await self._broadcast(
            EVENT_CHAT_MESSAGE, MessageResponse.from_message(message).model_dump(mode="json")
        )

    async def character_changed(self, character_id: UUID, recipients: set[UUID]) -> None:
        """Signale à ``recipients`` qu'un personnage a changé ou a été supprimé.

        L'événement ne porte que l'identifiant : la fiche se relit par l'API,
        qui applique les droits de chaque lecteur (US-009 · CA1, T3).
        """
        payload = {"type": EVENT_CHARACTER_CHANGED, "data": {"character_id": str(character_id)}}
        targets = [ws for ws, owner in self._connections.items() if owner in recipients]
        await asyncio.gather(*(self._send(ws, payload) for ws in targets))

    async def images_changed(self) -> None:
        """Signale à tous un changement des images de la table ou de la bibliothèque.

        L'événement ne porte aucune donnée : chacun relit la scène par l'API,
        qui produit des liens de lecture signés (03-A2, 04b).
        """
        await self._broadcast(EVENT_IMAGES_CHANGED, {})

    async def close_account(self, account_id: UUID, code: int) -> None:
        """Ferme toutes les connexions d'un compte (déconnexion, US-003 et T3)."""
        targets = [ws for ws, owner in self._connections.items() if owner == account_id]
        await asyncio.gather(*(self._close(ws, code) for ws in targets))

    async def _broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        payload = {"type": event_type, "data": data}
        await asyncio.gather(*(self._send(ws, payload) for ws in list(self._connections)))

    async def _send(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        """Envoie un événement. Une connexion qui ne répond plus est abandonnée.

        La boucle de lecture de cette connexion constate ensuite la fermeture et
        signale le départ du participant.
        """
        try:
            await asyncio.wait_for(websocket.send_json(payload), _SEND_TIMEOUT_SECONDS)
        except Exception:
            logger.info("Connexion temps réel abandonnée : envoi impossible")
            self.remove(websocket)
            await self._close(websocket, 1011)

    async def _close(self, websocket: WebSocket, code: int) -> None:
        """Ferme une connexion sans échouer si elle l'est déjà."""
        try:
            await websocket.close(code=code)
        except Exception:
            logger.debug("Connexion temps réel déjà fermée")
