"""Modèles de sortie de la table de jeu et du temps réel."""

from uuid import UUID

from pydantic import BaseModel

from app.services.table import TableState


class GmPresence(BaseModel):
    """Présence du MJ ([Siège — Maître du jeu (informatif)])."""

    display_name: str | None
    online: bool


class SeatResponse(BaseModel):
    """Place d'un joueur autour de la table."""

    position: int
    account_id: UUID
    display_name: str
    online: bool


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
                )
                for seat in state.seats
            ],
        )


class TicketResponse(BaseModel):
    """Ticket à usage unique ouvrant la connexion temps réel."""

    ticket: str
    expires_in: int
