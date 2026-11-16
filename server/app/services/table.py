"""Cas d'usage de la table de jeu : présence des participants (US-012, US-028).

L'état de présence vit en mémoire, pour la durée de vie du serveur (Q03-7).
Il suffit à une instance unique (CDC 12.3) ; plusieurs instances demanderaient
un stockage partagé.
"""

from dataclasses import dataclass
from typing import Protocol

from app.domain.accounts import Account, Role
from app.domain.table import Seat, SeatMap


@dataclass(frozen=True, slots=True)
class TableState:
    """Présence autour de la table, telle qu'elle est diffusée aux participants.

    Attributs:
        gm_name: nom affiché du MJ, ``None`` tant que son compte n'existe pas.
        gm_online: présence du MJ (US-012 · CA2).
        seats: places attribuées aux joueurs, dans l'ordre des positions.
    """

    gm_name: str | None
    gm_online: bool
    seats: list[Seat]


class GmDirectory(Protocol):
    """Accès au compte du MJ attendu par le service."""

    async def get_gm(self) -> Account | None: ...


class TableBroadcaster(Protocol):
    """Diffusion en temps réel de l'état de la table."""

    async def table_changed(self, state: TableState) -> None: ...


class TableService:
    """Suit les entrées et sorties des participants et diffuse l'état de la table.

    Args:
        accounts: accès au compte du MJ, pour afficher son nom même absent.
        broadcaster: diffusion en temps réel vers les participants connectés.
    """

    def __init__(self, accounts: GmDirectory, broadcaster: TableBroadcaster) -> None:
        self._accounts = accounts
        self._broadcaster = broadcaster
        self._seats = SeatMap()
        self._gm_connections = 0
        self._gm_name: str | None = None

    async def enter(self, account: Account) -> None:
        """Enregistre l'arrivée d'une connexion et diffuse le nouvel état (03-A6).

        Raises:
            TableFullError: si le joueur n'a pas de place et qu'aucune n'est libre.
        """
        if account.role is Role.GM:
            self._gm_connections += 1
            self._gm_name = account.display_name
        else:
            self._seats.enter(account.id, account.display_name)
        await self._broadcaster.table_changed(await self.state())

    async def leave(self, account: Account) -> None:
        """Enregistre la fermeture d'une connexion et diffuse le nouvel état (03-E2)."""
        if account.role is Role.GM:
            self._gm_connections = max(0, self._gm_connections - 1)
        else:
            self._seats.leave(account.id)
        await self._broadcaster.table_changed(await self.state())

    async def state(self) -> TableState:
        """Retourne l'état courant de la table."""
        if self._gm_name is None:
            gm = await self._accounts.get_gm()
            self._gm_name = gm.display_name if gm else None
        return TableState(
            gm_name=self._gm_name,
            gm_online=self._gm_connections > 0,
            seats=self._seats.seats(),
        )
