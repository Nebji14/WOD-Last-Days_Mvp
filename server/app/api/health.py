"""Route de santé, utilisée par l'hébergeur et par la tâche de maintien en éveil."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health() -> dict[str, str]:
    """Indique que le serveur répond."""
    return {"status": "ok"}
