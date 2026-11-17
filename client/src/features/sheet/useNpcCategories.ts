"use client";

/**
 * Catégories de PNJ lues par la fiche d'un PNJ (07, D1 et Q04c-1) : chemin de
 * la catégorie dans le titre, liste de choix en mode modification. Rien n'est
 * demandé pour un personnage joueur.
 */
import { useEffect, useState } from "react";

import { fetchDirectory, type NpcCategory } from "@/features/npcs/api";

const NONE: readonly NpcCategory[] = [];

/**
 * @param isNpc la fiche est celle d'un PNJ.
 * @param categoryId catégorie actuelle : un changement relit la liste.
 */
export function useNpcCategories(
  isNpc: boolean,
  categoryId: string | null,
): readonly NpcCategory[] {
  const [categories, setCategories] = useState<readonly NpcCategory[]>(NONE);

  useEffect(() => {
    if (!isNpc) {
      return;
    }
    let active = true;
    fetchDirectory()
      .then((directory) => {
        if (active) {
          setCategories(directory.categories);
        }
      })
      .catch((error: unknown) => console.warn("Catégories de PNJ indisponibles", error));
    return () => {
      active = false;
    };
  }, [isNpc, categoryId]);

  return isNpc ? categories : NONE;
}
