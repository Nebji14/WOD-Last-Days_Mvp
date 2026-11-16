"""Tickets de connexion temps réel : usage unique et durée de vie."""

from uuid import uuid4

from app.realtime.tickets import TICKET_TTL_SECONDS, TicketStore


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_ticket_is_consumed_once() -> None:
    store = TicketStore()
    account_id = uuid4()
    value = store.issue(account_id, session_expires_at=5000.0)

    ticket = store.consume(value)

    assert ticket is not None
    assert (ticket.account_id, ticket.session_expires_at) == (account_id, 5000.0)
    assert store.consume(value) is None


def test_unknown_ticket_is_refused() -> None:
    assert TicketStore().consume("inconnu") is None


def test_ticket_expires() -> None:
    clock = _Clock()
    store = TicketStore(clock)
    value = store.issue(uuid4(), session_expires_at=5000.0)

    clock.now += TICKET_TTL_SECONDS

    assert store.consume(value) is None


def test_tickets_are_unpredictable_and_distinct() -> None:
    store = TicketStore()
    account_id = uuid4()

    values = {store.issue(account_id, 5000.0) for _ in range(50)}

    assert len(values) == 50
    assert all(len(value) >= 40 for value in values)
