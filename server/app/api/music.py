"""Routes de la musique : recherche, commandes de lecture et file d'attente.

Tout est réservé au MJ, sauf la lecture en cours, que tout participant entend.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.deps import ContainerDep, CurrentAccount, CurrentGm, enforce_rate_limit
from app.domain.music import SEARCH_QUERY_MAX, SUGGESTION_QUERY_MAX, SUGGESTION_QUERY_MIN
from app.schemas.music import (
    DeckResponse,
    MoveItemRequest,
    NowPlayingResponse,
    PlayRequest,
    RepeatRequest,
    SearchResponse,
    SeekRequest,
    SkipRequest,
    SuggestionsResponse,
    TrackRequest,
    TrackResponse,
    VideoRequest,
)

_SEARCH_WINDOW_SECONDS = 60.0
_SEARCH_LIMIT = 20
_SUGGESTION_LIMIT = 90
_NO_CONTENT = status.HTTP_204_NO_CONTENT

router = APIRouter(prefix="/api/music", tags=["music"])


@router.get("")
async def now_playing(container: ContainerDep, _account: CurrentAccount) -> NowPlayingResponse:
    """Morceau en cours et position, pour tout participant."""
    return NowPlayingResponse.from_now(container.music_service.now_playing())


@router.get("/deck")
async def get_deck(container: ContainerDep, _gm: CurrentGm) -> DeckResponse:
    """Lecture, file d'attente et boucle."""
    return DeckResponse.from_deck(container.music_service.deck())


@router.get("/search")
async def search(
    container: ContainerDep,
    gm: CurrentGm,
    q: Annotated[str, Query(min_length=1, max_length=SEARCH_QUERY_MAX)],
) -> SearchResponse:
    """Cherche des morceaux par texte, ou retrouve celui d'un lien collé."""
    enforce_rate_limit(
        container.rate_limiter, f"music:search:{gm.id}", _SEARCH_LIMIT, _SEARCH_WINDOW_SECONDS
    )
    tracks = await container.music_catalog.search(q)
    return SearchResponse(tracks=[TrackResponse.from_track(track) for track in tracks])


@router.get("/suggestions")
async def suggest(
    container: ContainerDep,
    gm: CurrentGm,
    q: Annotated[
        str, Query(min_length=SUGGESTION_QUERY_MIN, max_length=SUGGESTION_QUERY_MAX)
    ],
) -> SuggestionsResponse:
    """Propose des recherches pour un texte en cours de saisie."""
    enforce_rate_limit(
        container.rate_limiter,
        f"music:suggest:{gm.id}",
        _SUGGESTION_LIMIT,
        _SEARCH_WINDOW_SECONDS,
    )
    return SuggestionsResponse(suggestions=await container.music_suggestions.suggest(q))


# --- Lecture -------------------------------------------------------------------------------


@router.post("/play", status_code=_NO_CONTENT)
async def play(payload: PlayRequest, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Diffuse un morceau à toute la table, tout de suite, avec ou sans sa vidéo."""
    track = await container.music_catalog.track(payload.video_id)
    await container.music_service.play(track, payload.show_video)
    return Response(status_code=_NO_CONTENT)


@router.put("/video", status_code=_NO_CONTENT)
async def show_video(payload: VideoRequest, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Affiche ou range, chez tous, la vidéo du morceau en cours."""
    await container.music_service.show_video(payload.shown)
    return Response(status_code=_NO_CONTENT)


@router.post("/pause", status_code=_NO_CONTENT)
async def pause(container: ContainerDep, _gm: CurrentGm) -> Response:
    """Met la musique en pause chez tous."""
    await container.music_service.pause()
    return Response(status_code=_NO_CONTENT)


@router.post("/resume", status_code=_NO_CONTENT)
async def resume(container: ContainerDep, _gm: CurrentGm) -> Response:
    """Reprend la musique chez tous."""
    await container.music_service.resume()
    return Response(status_code=_NO_CONTENT)


@router.post("/stop", status_code=_NO_CONTENT)
async def stop(container: ContainerDep, _gm: CurrentGm) -> Response:
    """Arrête la musique ; la file est conservée."""
    await container.music_service.stop()
    return Response(status_code=_NO_CONTENT)


@router.post("/skip", status_code=_NO_CONTENT)
async def skip(payload: SkipRequest, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Passe au morceau suivant, si la lecture visée est toujours en cours."""
    await container.music_service.skip(payload.play_id)
    return Response(status_code=_NO_CONTENT)


@router.put("/position", status_code=_NO_CONTENT)
async def seek(payload: SeekRequest, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Place la lecture à une position, chez tous."""
    await container.music_service.seek(payload.seconds)
    return Response(status_code=_NO_CONTENT)


@router.put("/repeat", status_code=_NO_CONTENT)
async def set_repeat(payload: RepeatRequest, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Choisit la boucle : aucune, le morceau ou la file."""
    await container.music_service.set_repeat(payload.mode)
    return Response(status_code=_NO_CONTENT)


# --- File d'attente ------------------------------------------------------------------------


@router.post("/queue", status_code=_NO_CONTENT)
async def enqueue(payload: TrackRequest, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Ajoute un morceau en fin de file."""
    await container.music_service.enqueue(await container.music_catalog.track(payload.video_id))
    return Response(status_code=_NO_CONTENT)


@router.delete("/queue", status_code=_NO_CONTENT)
async def clear_queue(container: ContainerDep, _gm: CurrentGm) -> Response:
    """Vide la file sans arrêter le morceau en cours."""
    await container.music_service.clear_queue()
    return Response(status_code=_NO_CONTENT)


@router.post("/queue/{item_id}/play", status_code=_NO_CONTENT)
async def play_item(item_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Diffuse tout de suite un morceau de la file."""
    await container.music_service.play_item(item_id)
    return Response(status_code=_NO_CONTENT)


@router.put("/queue/{item_id}/index", status_code=_NO_CONTENT)
async def move_item(
    item_id: UUID, payload: MoveItemRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Déplace un morceau dans la file."""
    await container.music_service.move(item_id, payload.index)
    return Response(status_code=_NO_CONTENT)


@router.delete("/queue/{item_id}", status_code=_NO_CONTENT)
async def remove_item(item_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Retire un morceau de la file."""
    await container.music_service.remove(item_id)
    return Response(status_code=_NO_CONTENT)
