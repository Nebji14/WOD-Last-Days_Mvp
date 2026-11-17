"""Arborescences sans cycle : dossiers d'images et catégories de PNJ.

Règle pure, sans accès réseau ni base.
"""

from collections.abc import Mapping
from uuid import UUID


def would_create_cycle(
    parents: Mapping[UUID, UUID | None], node_id: UUID, new_parent_id: UUID | None
) -> bool:
    """Indique si ranger ``node_id`` sous ``new_parent_id`` créerait un cycle.

    Args:
        parents: parent de chaque nœud existant.
        node_id: nœud déplacé.
        new_parent_id: futur parent, ``None`` pour la racine.

    Returns:
        ``True`` si le futur parent est le nœud lui-même ou l'un de ses descendants.
    """
    current = new_parent_id
    visited: set[UUID] = set()
    while current is not None and current not in visited:
        if current == node_id:
            return True
        visited.add(current)
        current = parents.get(current)
    return False
