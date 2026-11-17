"""Images de la table : image affichée en grand et pile (03-A2, 03-I5, 04b, 08a).

Vision maquette retenue (Q03MJ-1) : une seule image en grand, partie en pause
pour tous, puis posée sur la pile. Seul le MJ affiche, repose ou retire une
image (droit contrôlé par les routes) ; tous les participants lisent la scène.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.core.errors import AppError, ErrorCode
from app.domain.images import Image, table_pile
from app.services.image_links import UrlSigner, image_links
from app.services.images import ImageBroadcaster


class SceneStore(Protocol):
    """Accès à l'état des images de la table attendu par le service."""

    async def list_images(self) -> list[Image]: ...
    async def get_image(self, image_id: UUID) -> Image | None: ...
    async def show(self, image_id: UUID) -> None: ...
    async def put_down(self) -> UUID | None: ...
    async def remove_from_table(self, image_id: UUID) -> None: ...


@dataclass(frozen=True, slots=True)
class TableScene:
    """Ce que voient tous les participants.

    Attributs:
        shown: image affichée en grand, ``None`` hors pause (03-E5).
        pile: images posées, la plus récente en premier.
        links: lien de lecture de chaque image, par identifiant.
    """

    shown: Image | None
    pile: list[Image]
    links: dict[str, str]


class ImageTableService:
    """Cas d'usage de la scène de la table.

    Args:
        store: accès à l'état des images.
        signer: signature des liens de lecture.
        broadcaster: signal temps réel vers tous les participants.
    """

    def __init__(self, store: SceneStore, signer: UrlSigner, broadcaster: ImageBroadcaster) -> None:
        self._store = store
        self._signer = signer
        self._broadcaster = broadcaster

    async def scene(self) -> TableScene:
        """Retourne l'image affichée et la pile (US-012 · CA4, US-028 · CA3)."""
        images = await self._store.list_images()
        shown = next((image for image in images if image.is_shown), None)
        pile = table_pile(images)
        visible = pile + ([shown] if shown else [])
        return TableScene(shown, pile, await image_links(self._signer, visible))

    async def show(self, image_id: UUID) -> None:
        """Affiche l'image en grand chez tous : la table se met en pause (04b-I3)."""
        if await self._store.get_image(image_id) is None:
            raise AppError(ErrorCode.NOT_FOUND, "Image introuvable.", status_code=404)
        await self._store.show(image_id)
        await self._broadcaster.images_changed()

    async def put_down(self) -> None:
        """Referme l'image affichée : elle se pose sur la pile (04b-I4, Q04b-1)."""
        if await self._store.put_down() is not None:
            await self._broadcaster.images_changed()

    async def remove_from_table(self, image_id: UUID) -> None:
        """Retire une image de la table sans la supprimer (04b-I6, US-031 · CA6)."""
        if await self._store.get_image(image_id) is None:
            raise AppError(ErrorCode.NOT_FOUND, "Image introuvable.", status_code=404)
        await self._store.remove_from_table(image_id)
        await self._broadcaster.images_changed()
