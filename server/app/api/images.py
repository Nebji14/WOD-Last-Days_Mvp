"""Routes des images : bibliothèque du MJ et images montrées à la table.

La bibliothèque et les actions sur la table sont réservées au MJ.
La scène de la table se lit par tout participant connecté.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response, status

from app.api.deps import ContainerDep, CurrentAccount, CurrentGm, enforce_rate_limit
from app.api.uploads import read_body
from app.domain.images import MAX_IMAGE_BYTES
from app.schemas.images import (
    CreatedResponse,
    FolderRenameRequest,
    FolderRequest,
    ImageResponse,
    LibraryResponse,
    MoveFolderRequest,
    MoveImageRequest,
    RenameRequest,
    SceneResponse,
)

_UPLOAD_WINDOW_SECONDS = 60.0
_UPLOAD_LIMIT = 60
_NO_CONTENT = status.HTTP_204_NO_CONTENT

router = APIRouter(prefix="/api", tags=["images"])


# --- Bibliothèque (MJ) ---------------------------------------------------------------------


@router.get("/images")
async def get_library(container: ContainerDep, _gm: CurrentGm) -> LibraryResponse:
    """Retourne la bibliothèque complète."""
    return LibraryResponse.from_library(await container.image_service.library())


@router.post("/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    request: Request,
    container: ContainerDep,
    gm: CurrentGm,
    filename: Annotated[str, Query(min_length=1, max_length=255)],
    folder_id: Annotated[UUID | None, Query()] = None,
) -> ImageResponse:
    """Ajoute une image envoyée telle quelle dans le corps de la requête."""
    enforce_rate_limit(
        container.rate_limiter, f"images:upload:{gm.id}", _UPLOAD_LIMIT, _UPLOAD_WINDOW_SECONDS
    )
    content = await read_body(request, MAX_IMAGE_BYTES)
    image = await container.image_service.upload(filename, folder_id, content)
    return ImageResponse.from_image(image, {})


@router.patch("/images/{image_id}", status_code=_NO_CONTENT)
async def rename_image(
    image_id: UUID, payload: RenameRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Renomme une image."""
    await container.image_service.rename_image(image_id, payload.name)
    return Response(status_code=_NO_CONTENT)


@router.put("/images/{image_id}/folder", status_code=_NO_CONTENT)
async def move_image(
    image_id: UUID, payload: MoveImageRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Range une image dans un dossier."""
    await container.image_service.move_image(image_id, payload.folder_id)
    return Response(status_code=_NO_CONTENT)


@router.delete("/images/{image_id}", status_code=_NO_CONTENT)
async def delete_image(image_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Supprime une image de la bibliothèque, et de la table si elle y est."""
    await container.image_service.delete_image(image_id)
    return Response(status_code=_NO_CONTENT)


@router.post("/image-folders", status_code=status.HTTP_201_CREATED)
async def create_folder(
    payload: FolderRequest, container: ContainerDep, _gm: CurrentGm
) -> CreatedResponse:
    """Crée un dossier, à la racine ou dans un dossier."""
    folder_id = await container.image_service.create_folder(payload.name, payload.parent_id)
    return CreatedResponse(id=folder_id)


@router.patch("/image-folders/{folder_id}", status_code=_NO_CONTENT)
async def rename_folder(
    folder_id: UUID, payload: FolderRenameRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Renomme un dossier."""
    await container.image_service.rename_folder(folder_id, payload.name)
    return Response(status_code=_NO_CONTENT)


@router.put("/image-folders/{folder_id}/parent", status_code=_NO_CONTENT)
async def move_folder(
    folder_id: UUID, payload: MoveFolderRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Range un dossier sous un autre ; refusé s'il créerait un cycle."""
    await container.image_service.move_folder(folder_id, payload.parent_id)
    return Response(status_code=_NO_CONTENT)


@router.delete("/image-folders/{folder_id}", status_code=_NO_CONTENT)
async def delete_folder(folder_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Supprime un dossier ; son contenu remonte au parent."""
    await container.image_service.delete_folder(folder_id)
    return Response(status_code=_NO_CONTENT)


# --- Table ---------------------------------------------------------------------------------


@router.get("/table/images")
async def get_scene(container: ContainerDep, _account: CurrentAccount) -> SceneResponse:
    """Image affichée en grand et pile, pour tout participant."""
    return SceneResponse.from_scene(await container.image_table_service.scene())


@router.post("/table/images/{image_id}/show", status_code=_NO_CONTENT)
async def show_image(image_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Affiche une image en grand chez tous ; la table se met en pause."""
    await container.image_table_service.show(image_id)
    return Response(status_code=_NO_CONTENT)


@router.post("/table/images/put-down", status_code=_NO_CONTENT)
async def put_down_image(container: ContainerDep, _gm: CurrentGm) -> Response:
    """Referme l'image affichée : elle se pose sur la pile."""
    await container.image_table_service.put_down()
    return Response(status_code=_NO_CONTENT)


@router.delete("/table/images/{image_id}", status_code=_NO_CONTENT)
async def remove_from_table(image_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Retire une image de la table sans la supprimer."""
    await container.image_table_service.remove_from_table(image_id)
    return Response(status_code=_NO_CONTENT)
