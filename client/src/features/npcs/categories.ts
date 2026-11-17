/** Catégories de PNJ : contenu et compteurs, sous-catégories comprises. */
import { byName, nodePath, subtreeIds } from "@/shared/tree";

import type { NpcCard, NpcCategory } from "./api";

/** PNJ de la catégorie et de ses sous-catégories ; `null` : tous les PNJ. */
export function npcsIn(
  npcs: readonly NpcCard[],
  categories: readonly NpcCategory[],
  categoryId: string | null,
): NpcCard[] {
  if (categoryId === null) {
    return [...npcs].sort(byName);
  }
  const ids = subtreeIds(categories, categoryId);
  return npcs.filter((npc) => npc.categoryId !== null && ids.has(npc.categoryId)).sort(byName);
}

/** Nombre de PNJ de chaque catégorie, sous-catégories comprises. */
export function categoryCounts(
  npcs: readonly NpcCard[],
  categories: readonly NpcCategory[],
): Map<string, number> {
  return new Map(
    categories.map((category) => [category.id, npcsIn(npcs, categories, category.id).length]),
  );
}

/** Chemin lisible d'une catégorie : « Antagonistes › Culte ». */
export function categoryLabel(
  categories: readonly NpcCategory[],
  categoryId: string | null,
): string {
  return nodePath(categories, categoryId)
    .map((category) => category.name)
    .join(" › ");
}
