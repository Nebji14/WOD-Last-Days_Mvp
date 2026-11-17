"""Cas d'usage de l'outil Joueurs du MJ (écran 04a, US-025).

Le droit d'accès (MJ uniquement) est contrôlé par la route.
"""

from typing import Protocol
from uuid import UUID

from app.domain.players import PlayerRecord, PlayerSummary, order_players


class PlayerDirectory(Protocol):
    """Lecture des comptes joueurs attendue par le service."""

    async def list_players(self) -> list[PlayerRecord]: ...


class PresenceSource(Protocol):
    """Présence des joueurs autour de la table."""

    def online_accounts(self) -> set[UUID]: ...


class PlayerService:
    """Assemble la liste des joueurs et leur présence.

    Args:
        players: lecture des comptes joueurs et de leurs personnages.
        presence: comptes actuellement connectés à la table.
    """

    def __init__(self, players: PlayerDirectory, presence: PresenceSource) -> None:
        self._players = players
        self._presence = presence

    async def list_players(self) -> list[PlayerSummary]:
        """Retourne tous les joueurs, connectés d'abord (US-025 · CA1, CA2 ; Q04a-2)."""
        online = self._presence.online_accounts()
        records = await self._players.list_players()
        return order_players(
            PlayerSummary(record=record, online=record.account.id in online) for record in records
        )
