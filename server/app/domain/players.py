"""Joueurs vus par le MJ dans l'outil Joueurs (écran 04a, US-025).

Règles pures, sans accès réseau ni base.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.accounts import Account


@dataclass(frozen=True, slots=True)
class PlayerRecord:
    """Compte joueur et noms de ses personnages, tels que stockés.

    Attributs:
        character_names: nom de chaque personnage, du plus ancien au plus récent ;
            vide pour un joueur sans personnage (US-025 · CA1).
    """

    account: Account
    character_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlayerSummary:
    """Ligne de la liste des joueurs : compte, personnages et présence (US-025 · CA2)."""

    record: PlayerRecord
    online: bool


def order_players(players: Iterable[PlayerSummary]) -> list[PlayerSummary]:
    """Range les joueurs : connectés d'abord, puis par nom affiché (Q04a-2).

    L'ordre alphabétique ignore la casse ; le nom d'utilisateur départage deux
    noms affichés identiques, pour un ordre stable.
    """
    return sorted(
        players,
        key=lambda player: (
            not player.online,
            player.record.account.display_name.casefold(),
            player.record.account.username.casefold(),
        ),
    )
