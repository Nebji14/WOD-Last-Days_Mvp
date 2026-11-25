"""Routes des portraits : image propre à chaque forme d'un personnage."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Request, Response, status

from app.api.characters import SheetWrite
from app.api.deps import ContainerDep, CurrentAccount, enforce_rate_limit
from app.api.uploads import read_body
from app.domain.portraits import (
    MAX_ORIGINAL_BYTES,
    MAX_PORTRAIT_BYTES,
    PORTRAIT_NAME_PATTERN,
)
from app.schemas.characters import AnyCharacterResponse, character_response
from app.services.portraits import PortraitFile

_UPLOAD_WINDOW_SECONDS = 60.0
# Deux fichiers par photo : le portrait cadré et la photo entière.
_UPLOAD_LIMIT = 40
# Le nom change avec l'image : une copie gardée par le navigateur reste juste.
_CACHE_CONTROL = "private, max-age=86400, immutable"

PortraitName = Annotated[str, Path(pattern=PORTRAIT_NAME_PATTERN)]

router = APIRouter(prefix="/api", tags=["portraits"])


@router.put("/sheets/{sheet_id}/portrait", dependencies=[SheetWrite])
async def replace_portrait(
    sheet_id: UUID, request: Request, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Donne une image à une forme ; le fichier est envoyé tel quel."""
    limit_portrait_uploads(container, account)
    content = await read_body(request, MAX_PORTRAIT_BYTES)
    character = await container.portrait_service.replace(account, sheet_id, content)
    return character_response(character, account)


@router.delete("/sheets/{sheet_id}/portrait", dependencies=[SheetWrite])
async def remove_portrait(
    sheet_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Retire l'image d'une forme."""
    character = await container.portrait_service.remove(account, sheet_id)
    return character_response(character, account)


@router.get("/portraits/{name}")
async def get_portrait(
    name: PortraitName, container: ContainerDep, account: CurrentAccount
) -> Response:
    """Retourne une image que le lecteur a le droit de voir."""
    portrait = await container.portrait_service.read(account, name)
    return _image_response(portrait, _CACHE_CONTROL)


@router.get("/portraits/{name}/original")
async def get_original(
    name: PortraitName, container: ContainerDep, account: CurrentAccount
) -> Response:
    """Retourne la photo entière, à qui peut recadrer le portrait."""
    original = await container.portrait_service.read_original(account, name)
    return _image_response(original, "no-store")


@router.put(
    "/portraits/{name}/original",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[SheetWrite],
)
async def store_original(
    name: PortraitName, request: Request, container: ContainerDep, account: CurrentAccount
) -> Response:
    """Garde la photo entière d'un portrait ; le fichier est envoyé tel quel."""
    limit_portrait_uploads(container, account)
    content = await read_body(request, MAX_ORIGINAL_BYTES)
    await container.portrait_service.store_original(account, name, content)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def limit_portrait_uploads(container: ContainerDep, account: CurrentAccount) -> None:
    """Borne le nombre de fichiers envoyés par compte."""
    enforce_rate_limit(
        container.rate_limiter,
        f"portraits:upload:{account.id}",
        _UPLOAD_LIMIT,
        _UPLOAD_WINDOW_SECONDS,
    )


def _image_response(file: PortraitFile, cache_control: str) -> Response:
    return Response(
        content=file.content,
        media_type=file.type.value,
        headers={"Cache-Control": cache_control},
    )
