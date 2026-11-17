"""Règles de la bibliothèque d'images (04b) : type réel, noms, dossiers, pile."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.hierarchy import would_create_cycle
from app.domain.images import (
    IMAGE_NAME_MAX,
    Image,
    ImageType,
    detect_image_type,
    image_name_from_filename,
    table_pile,
)
from app.domain.names import clean_name

PNG_HEAD = b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0d"


@pytest.mark.parametrize(
    ("head", "expected"),
    [
        (PNG_HEAD, ImageType.PNG),
        (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01", ImageType.JPEG),
        (b"RIFF\x24\x00\x00\x00WEBP", ImageType.WEBP),
        (b"GIF89a\x01\x00\x01\x00\x00\x00", ImageType.GIF),
        (b"<svg xmlns='http", None),
        (b"%PDF-1.7\n%\xe2\xe3\xcf\xd3", None),
        (b"", None),
    ],
)
def test_type_is_read_from_the_file_signature(head: bytes, expected: ImageType | None) -> None:
    assert detect_image_type(head) is expected


def test_image_name_is_the_file_name_without_extension() -> None:
    assert image_name_from_filename("Quai de nuit.final.png") == "Quai de nuit.final"
    assert image_name_from_filename("C:\\docs\\  Plan   du manoir .jpg") == "Plan du manoir"
    assert image_name_from_filename(".png") == "Image"
    assert len(image_name_from_filename("x" * 300 + ".png")) == IMAGE_NAME_MAX


def test_entered_names_are_trimmed_and_bounded() -> None:
    assert clean_name("  Les   docks ", 60) == "Les docks"
    assert clean_name("   ", 60) is None
    assert clean_name("x" * 61, 60) is None


def test_a_folder_cannot_move_under_itself_or_a_descendant() -> None:
    root, child, grandchild, other = uuid4(), uuid4(), uuid4(), uuid4()
    parents = {root: None, child: root, grandchild: child, other: None}

    assert would_create_cycle(parents, root, root)
    assert would_create_cycle(parents, root, grandchild)
    assert not would_create_cycle(parents, grandchild, other)
    assert not would_create_cycle(parents, child, None)


def _image(on_table_at: datetime | None) -> Image:
    return Image(uuid4(), "x", None, "a.png", "image/png", 1, False, on_table_at, datetime.now(UTC))


def test_pile_shows_the_most_recent_image_first() -> None:
    older = _image(datetime(2026, 11, 1, tzinfo=UTC))
    newer = _image(datetime(2026, 11, 2, tzinfo=UTC))
    absent = _image(None)

    assert table_pile([older, absent, newer]) == [newer, older]
