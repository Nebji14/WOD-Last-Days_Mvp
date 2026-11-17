"""Noms saisis dans l'interface : dossiers, images, catégories (04b, 04c).

Règle pure, sans accès réseau ni base.
"""


def clean_name(name: str, limit: int) -> str | None:
    """Nom saisi sans espaces superflus ; ``None`` s'il est vide ou trop long (04b, 04c-I2)."""
    cleaned = " ".join(name.split())
    if not cleaned or len(cleaned) > limit:
        return None
    return cleaned
