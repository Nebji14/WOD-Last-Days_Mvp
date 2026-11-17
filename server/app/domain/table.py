"""Règles métier de la table de jeu : places et présence.

Module pur : aucun accès réseau ni base de données.
"""

from dataclasses import dataclass
from uuid import UUID

# 10 utilisateurs simultanés au plus, MJ compris.
PLAYER_SEAT_COUNT = 9


class TableFullError(Exception):
    """Les neuf places de joueurs sont déjà attribuées."""


@dataclass(frozen=True, slots=True)
class Seat:
    """Place d'un joueur autour de la table.

    Attributs:
        position: rang de la place, de 0 à ``PLAYER_SEAT_COUNT - 1``.
        online: ``False`` quand le joueur a quitté la salle ; son siège reste
            affiché, atténué.
    """

    position: int
    account_id: UUID
    display_name: str
    online: bool


class SeatMap:
    """Attribution des places pour la durée de vie du serveur.

    Un joueur reçoit la première place libre à sa première entrée et la
    conserve ensuite, qu'il soit connecté ou non. Un même compte peut
    ouvrir plusieurs connexions (fenêtres détachées) : il reste en ligne
    tant qu'il en garde au moins une.
    """

    def __init__(self) -> None:
        self._positions: dict[UUID, int] = {}
        self._names: dict[UUID, str] = {}
        self._connections: dict[UUID, int] = {}

    def enter(self, account_id: UUID, display_name: str) -> None:
        """Enregistre une connexion du joueur et lui attribue une place au besoin.

        Raises:
            TableFullError: si le joueur n'a pas de place et qu'aucune n'est libre.
        """
        if account_id not in self._positions:
            taken = set(self._positions.values())
            free = next((p for p in range(PLAYER_SEAT_COUNT) if p not in taken), None)
            if free is None:
                raise TableFullError
            self._positions[account_id] = free
        self._names[account_id] = display_name
        self._connections[account_id] = self._connections.get(account_id, 0) + 1

    def leave(self, account_id: UUID) -> None:
        """Retire une connexion du joueur. Sa place lui reste attribuée."""
        remaining = self._connections.get(account_id, 0) - 1
        if remaining > 0:
            self._connections[account_id] = remaining
        else:
            self._connections.pop(account_id, None)

    def seats(self) -> list[Seat]:
        """Retourne les places attribuées, dans l'ordre des positions."""
        return sorted(
            (
                Seat(position, account_id, self._names[account_id], account_id in self._connections)
                for account_id, position in self._positions.items()
            ),
            key=lambda seat: seat.position,
        )
