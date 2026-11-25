"""Cas d'usage de la table de jeu : présence des participants.

L'état de présence vit en mémoire, pour la durée de vie du serveur.
Il suffit à une instance unique ; plusieurs instances demanderaient
un stockage partagé.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.domain.accounts import Account, Role
from app.domain.character import SeatCharacter
from app.domain.table import Seat, SeatMap


@dataclass(frozen=True, slots=True)
class TableState:
    """Présence autour de la table, telle qu'elle est diffusée aux participants.

    Attributs:
        gm_name: nom affiché du MJ, ``None`` tant que son compte n'existe pas.
        gm_portrait: photo du MJ, ``None`` sans photo.
        gm_online: présence du MJ.
        seats: places attribuées aux joueurs, dans l'ordre des positions.
        characters: personnage joué par compte ; un compte sans personnage en
            est absent.
    """

    gm_name: str | None
    gm_portrait: str | None
    gm_online: bool
    seats: list[Seat]
    characters: dict[UUID, SeatCharacter]


class GmDirectory(Protocol):
    """Accès au compte du MJ attendu par le service."""

    async def get_gm(self) -> Account | None: ...


class SeatCharacterDirectory(Protocol):
    """Accès au personnage joué par chaque compte."""

    async def played_by(self, account_ids: list[UUID]) -> dict[UUID, SeatCharacter]: ...


class TableBroadcaster(Protocol):
    """Diffusion en temps réel de l'état de la table."""

    async def table_changed(self, state: TableState) -> None: ...


class TableService:
    """Suit les entrées et sorties des participants et diffuse l'état de la table.

    Args:
        accounts: accès au compte du MJ, pour afficher son nom même absent.
        characters: accès au personnage joué par chaque joueur assis.
        broadcaster: diffusion en temps réel vers les participants connectés.
    """

    def __init__(
        self,
        accounts: GmDirectory,
        characters: SeatCharacterDirectory,
        broadcaster: TableBroadcaster,
    ) -> None:
        self._accounts = accounts
        self._characters = characters
        self._broadcaster = broadcaster
        self._seats = SeatMap()
        self._gm_connections = 0
        self._gm: Account | None = None

    async def enter(self, account: Account) -> None:
        """Enregistre l'arrivée d'une connexion et diffuse le nouvel état.

        Raises:
            TableFullError: si le joueur n'a pas de place et qu'aucune n'est libre.
        """
        if account.role is Role.GM:
            self._gm_connections += 1
            self._gm = account
        else:
            self._seats.enter(account.id, account.display_name)
        await self._broadcaster.table_changed(await self.state())

    async def leave(self, account: Account) -> None:
        """Enregistre la fermeture d'une connexion et diffuse le nouvel état."""
        if account.role is Role.GM:
            self._gm_connections = max(0, self._gm_connections - 1)
        else:
            self._seats.leave(account.id)
        await self._broadcaster.table_changed(await self.state())

    async def refresh_account(self, account: Account) -> None:
        """Affiche le nouveau nom ou la nouvelle photo d'un participant."""
        if account.role is Role.GM:
            self._gm = account
        else:
            self._seats.rename(account.id, account.display_name)
        await self.refresh()

    async def vacate(self, account_id: UUID) -> None:
        """Retire un joueur de la table et diffuse l'état."""
        self._seats.vacate(account_id)
        await self.refresh()

    async def refresh(self) -> None:
        """Rediffuse l'état de la table : un personnage joué a changé."""
        await self._broadcaster.table_changed(await self.state())

    def online_accounts(self) -> set[UUID]:
        """Joueurs actuellement connectés à la table."""
        return {seat.account_id for seat in self._seats.seats() if seat.online}

    async def state(self) -> TableState:
        """Retourne l'état courant de la table."""
        if self._gm is None:
            self._gm = await self._accounts.get_gm()
        seats = self._seats.seats()
        return TableState(
            gm_name=self._gm.display_name if self._gm else None,
            gm_portrait=self._gm.portrait if self._gm else None,
            gm_online=self._gm_connections > 0,
            seats=seats,
            characters=await self._characters.played_by([seat.account_id for seat in seats]),
        )
