"""Tickets d'ouverture de la connexion temps réel.

Le navigateur ne joint pas les cookies de session au serveur temps réel, qui
n'est pas sur l'origine du client. Une session authentifiée demande donc un
ticket par l'API, puis le présente comme premier message de la connexion
WebSocket. Le ticket est aléatoire, à usage unique et de courte durée.

Stockage en mémoire : suffisant pour une instance unique (CDC 12.3).
"""

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

TICKET_TTL_SECONDS = 30
_TICKET_BYTES = 32


@dataclass(frozen=True, slots=True)
class Ticket:
    """Droit d'ouvrir une connexion temps réel.

    Attributs:
        session_expires_at: expiration de la session qui a demandé le ticket,
            en secondes depuis l'époque Unix. La connexion ne lui survit pas.
        valid_until: fin de validité du ticket, sur l'horloge du magasin.
    """

    account_id: UUID
    session_expires_at: float
    valid_until: float


class TicketStore:
    """Émet et consomme les tickets.

    Args:
        clock: source de temps monotone, remplaçable dans les tests.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._tickets: dict[str, Ticket] = {}

    def issue(self, account_id: UUID, session_expires_at: float) -> str:
        """Émet un ticket pour ce compte et retourne sa valeur."""
        now = self._clock()
        self._tickets = {
            value: ticket for value, ticket in self._tickets.items() if ticket.valid_until > now
        }
        value = secrets.token_urlsafe(_TICKET_BYTES)
        self._tickets[value] = Ticket(account_id, session_expires_at, now + TICKET_TTL_SECONDS)
        return value

    def consume(self, value: str) -> Ticket | None:
        """Retire le ticket et le retourne s'il est encore valide.

        Un ticket ne sert qu'une fois : un second appel retourne ``None``.
        """
        ticket = self._tickets.pop(value, None)
        if ticket is None or ticket.valid_until <= self._clock():
            return None
        return ticket
