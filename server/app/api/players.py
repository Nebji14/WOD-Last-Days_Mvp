"""Routes de l'outil Joueurs du MJ (écran 04a, US-025).

Réservées au MJ (CDC 8.3) : tout autre compte reçoit un refus.
"""

from fastapi import APIRouter

from app.api.deps import ContainerDep, CurrentGm
from app.schemas.players import PlayerListResponse, PlayerResponse

router = APIRouter(prefix="/api", tags=["players"])


@router.get("/players")
async def list_players(container: ContainerDep, _gm: CurrentGm) -> PlayerListResponse:
    """Liste tous les joueurs, connectés d'abord (US-025 · CA1, CA2 ; Q04a-2)."""
    players = await container.player_service.list_players()
    return PlayerListResponse(players=[PlayerResponse.from_summary(p) for p in players])
