"""Modèles de sortie de la table de jeu et du temps réel."""

from uuid import UUID

from pydantic import BaseModel

from app.services.table import TableState


class GmPresence(BaseModel):
    """Présence du MJ ([Siège — Maître du jeu (informatif)])."""

    display_name: str | None
    online: bool


class SeatCharacterResponse(BaseModel):
    """Personnage affiché sur un siège : nom, concept, santé et volonté (Q03-3)."""

    id: UUID
    name: str
    concept: str
    health_max: int
    wound_track: str
    willpower_max: int
    willpower_current: int


class SeatResponse(BaseModel):
    """Place d'un joueur autour de la table.

    Attributs:
        character: personnage joué, ``None`` si le joueur n'en a pas (03-E4).
    """

    position: int
    account_id: UUID
    display_name: str
    online: bool
    character: SeatCharacterResponse | None


class TableStateResponse(BaseModel):
    """État de présence de la table (US-012 · CA2, US-028 · CA1)."""

    gm: GmPresence
    seats: list[SeatResponse]

    @classmethod
    def from_state(cls, state: TableState) -> "TableStateResponse":
        """Projette l'état du service vers sa représentation publique."""
        return cls(
            gm=GmPresence(display_name=state.gm_name, online=state.gm_online),
            seats=[
                SeatResponse(
                    position=seat.position,
                    account_id=seat.account_id,
                    display_name=seat.display_name,
                    online=seat.online,
                    character=_seat_character(state, seat.account_id),
                )
                for seat in state.seats
            ],
        )


def _seat_character(state: TableState, account_id: UUID) -> SeatCharacterResponse | None:
    character = state.characters.get(account_id)
    if character is None:
        return None
    return SeatCharacterResponse(
        id=character.character_id,
        name=character.name,
        concept=character.concept,
        health_max=character.health_max,
        wound_track=character.wound_track,
        willpower_max=character.willpower_max,
        willpower_current=character.willpower_current,
    )


class TicketResponse(BaseModel):
    """Ticket à usage unique ouvrant la connexion temps réel."""

    ticket: str
    expires_in: int
