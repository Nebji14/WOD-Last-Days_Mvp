"""Routes de l'outil Joueurs du MJ.

Réservées au MJ : tout autre compte reçoit un refus.
"""

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import ContainerDep, CurrentGm
from app.schemas.players import PlayerListResponse, PlayerResponse

router = APIRouter(prefix="/api", tags=["players"])


@router.get("/players")
async def list_players(container: ContainerDep, _gm: CurrentGm) -> PlayerListResponse:
    """Liste tous les joueurs, connectés d'abord."""
    players = await container.player_service.list_players()
    return PlayerListResponse(players=[PlayerResponse.from_summary(p) for p in players])


@router.post("/players/{player_id}/reactivate", status_code=status.HTTP_204_NO_CONTENT)
async def reactivate_player(player_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Rend son accès à un joueur qui avait désactivé son compte."""
    await container.account_closure_service.reactivate(player_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
