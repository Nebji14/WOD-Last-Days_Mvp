"""Route d'accès au temps réel : émission du ticket de connexion."""

from fastapi import APIRouter, Depends

from app.api.deps import ContainerDep, CurrentSession, rate_limit
from app.realtime.tickets import TICKET_TTL_SECONDS
from app.schemas.table import TicketResponse

router = APIRouter(prefix="/api/realtime", tags=["realtime"])

_WINDOW_SECONDS = 60.0
_TICKET_LIMIT_PER_ADDRESS = 60


@router.post(
    "/ticket",
    dependencies=[
        Depends(rate_limit("realtime-ticket", _TICKET_LIMIT_PER_ADDRESS, _WINDOW_SECONDS))
    ],
)
async def issue_ticket(container: ContainerDep, session: CurrentSession) -> TicketResponse:
    """Émet un ticket à usage unique pour ouvrir la connexion WebSocket.

    La connexion ouverte avec ce ticket est fermée à l'expiration de la session.
    """
    ticket = container.tickets.issue(session.account.id, session.expires_at)
    return TicketResponse(ticket=ticket, expires_in=TICKET_TTL_SECONDS)
