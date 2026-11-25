"""Lecture d'un fichier envoyé tel quel dans le corps d'une requête."""

from fastapi import Request

from app.services.uploads import image_too_large


async def read_body(request: Request, max_bytes: int) -> bytes:
    """Lit le fichier envoyé, sans jamais dépasser ``max_bytes`` en mémoire.

    Raises:
        AppError: ``image_too_large`` dès que la limite est franchie.
    """
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > max_bytes:
        raise image_too_large()
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > max_bytes:
            raise image_too_large()
        chunks.append(chunk)
    return b"".join(chunks)
