"""Accès aux données de la bibliothèque d'images (tables ``image`` et ``image_folder``)."""

from uuid import UUID

import asyncpg

from app.domain.images import Image, ImageFolder

_IMAGE_COLUMNS = (
    "id, name, folder_id, storage_path, content_type, size_bytes, is_shown, on_table_at, created_at"
)


class PgImageRepository:
    """Dépôt des images et des dossiers sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    # --- Dossiers ------------------------------------------------------------------------

    async def list_folders(self) -> list[ImageFolder]:
        """Retourne tous les dossiers, par nom."""
        rows = await self._pool.fetch(
            "select id, name, parent_id from image_folder order by lower(name), id"
        )
        return [ImageFolder(row["id"], row["name"], row["parent_id"]) for row in rows]

    async def create_folder(self, name: str, parent_id: UUID | None) -> UUID:
        """Crée un dossier et retourne son identifiant."""
        folder_id: UUID = await self._pool.fetchval(
            "insert into image_folder (name, parent_id) values ($1, $2) returning id",
            name,
            parent_id,
        )
        return folder_id

    async def rename_folder(self, folder_id: UUID, name: str) -> bool:
        """Renomme un dossier. Retourne ``False`` s'il n'existe pas."""
        status = await self._pool.execute(
            "update image_folder set name = $2 where id = $1", folder_id, name
        )
        return str(status).endswith(" 1")

    async def move_folder(self, folder_id: UUID, parent_id: UUID | None) -> None:
        """Range un dossier sous un autre, ou à la racine."""
        await self._pool.execute(
            "update image_folder set parent_id = $2 where id = $1", folder_id, parent_id
        )

    async def delete_folder(self, folder_id: UUID, parent_id: UUID | None) -> None:
        """Supprime un dossier ; ses images et sous-dossiers remontent au parent (Q04b-4)."""
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "update image set folder_id = $2 where folder_id = $1", folder_id, parent_id
            )
            await connection.execute(
                "update image_folder set parent_id = $2 where parent_id = $1",
                folder_id,
                parent_id,
            )
            await connection.execute("delete from image_folder where id = $1", folder_id)

    # --- Images --------------------------------------------------------------------------

    async def list_images(self) -> list[Image]:
        """Retourne toutes les images, par nom."""
        rows = await self._pool.fetch(
            f"select {_IMAGE_COLUMNS} from image order by lower(name), id"  # noqa: S608
        )
        return [_to_image(row) for row in rows]

    async def get_image(self, image_id: UUID) -> Image | None:
        """Retourne l'image, ou ``None``."""
        row = await self._pool.fetchrow(
            f"select {_IMAGE_COLUMNS} from image where id = $1",  # noqa: S608
            image_id,
        )
        return _to_image(row) if row else None

    async def create_image(
        self,
        name: str,
        folder_id: UUID | None,
        storage_path: str,
        content_type: str,
        size_bytes: int,
    ) -> UUID:
        """Enregistre une image déjà déposée dans le stockage."""
        image_id: UUID = await self._pool.fetchval(
            "insert into image (name, folder_id, storage_path, content_type, size_bytes) "
            "values ($1, $2, $3, $4, $5) returning id",
            name,
            folder_id,
            storage_path,
            content_type,
            size_bytes,
        )
        return image_id

    async def rename_image(self, image_id: UUID, name: str) -> None:
        """Renomme une image (04b-I5)."""
        await self._pool.execute("update image set name = $2 where id = $1", image_id, name)

    async def move_image(self, image_id: UUID, folder_id: UUID | None) -> None:
        """Range une image dans un dossier, ou à la racine (04b-I10)."""
        await self._pool.execute(
            "update image set folder_id = $2 where id = $1", image_id, folder_id
        )

    async def delete_image(self, image_id: UUID) -> None:
        """Supprime la ligne de l'image (le fichier est supprimé par le service)."""
        await self._pool.execute("delete from image where id = $1", image_id)

    # --- Scène de la table -------------------------------------------------------------

    async def show(self, image_id: UUID) -> None:
        """Affiche l'image en grand ; une image déjà affichée est posée sur la pile."""
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute(
                "update image set is_shown = false, on_table_at = now() "
                "where is_shown and id <> $1",
                image_id,
            )
            await connection.execute("update image set is_shown = true where id = $1", image_id)

    async def put_down(self) -> UUID | None:
        """Pose l'image affichée sur la pile (04b-I4). Retourne son identifiant, ou ``None``."""
        image_id: UUID | None = await self._pool.fetchval(
            "update image set is_shown = false, on_table_at = now() where is_shown returning id"
        )
        return image_id

    async def remove_from_table(self, image_id: UUID) -> None:
        """Retire l'image de la table sans la supprimer (04b-I6, US-031 · CA6)."""
        await self._pool.execute(
            "update image set on_table_at = null, is_shown = false where id = $1", image_id
        )


def _to_image(row: asyncpg.Record) -> Image:
    """Convertit une ligne de la table en objet du domaine."""
    return Image(
        id=row["id"],
        name=row["name"],
        folder_id=row["folder_id"],
        storage_path=row["storage_path"],
        content_type=row["content_type"],
        size_bytes=row["size_bytes"],
        is_shown=row["is_shown"],
        on_table_at=row["on_table_at"],
        created_at=row["created_at"],
    )
