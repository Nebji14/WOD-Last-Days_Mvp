import { describe, expect, it } from "vitest";

import type { NpcCard, NpcCategory } from "./api";
import { categoryCounts, categoryLabel, npcsIn } from "./categories";

const categories: NpcCategory[] = [
  { id: "villains", name: "Antagonistes", parentId: null },
  { id: "cult", name: "Culte", parentId: "villains" },
  { id: "allies", name: "Alliés", parentId: null },
];

function npc(id: string, name: string, categoryId: string | null): NpcCard {
  return {
    id,
    name,
    concept: "",
    model: "simplified",
    categoryId,
    healthMax: 5,
    willpowerMax: 3,
    power: 1,
    finesse: 1,
    resilience: 1,
  };
}

const npcs = [
  npc("priest", "Le Prêtre rouge", "cult"),
  npc("widow", "La Veuve", "cult"),
  npc("boss", "Le Commandeur", "villains"),
  npc("loose", "Inconnu", null),
];

describe("04c · catégories (Q04c-4)", () => {
  it("montre les PNJ de la catégorie et de ses sous-catégories", () => {
    expect(npcsIn(npcs, categories, "villains").map((n) => n.id)).toEqual([
      "widow",
      "boss",
      "priest",
    ]);
    expect(npcsIn(npcs, categories, "cult")).toHaveLength(2);
    expect(npcsIn(npcs, categories, null)).toHaveLength(4);
  });

  it("compte les PNJ sous-catégories comprises", () => {
    const counts = categoryCounts(npcs, categories);
    expect(counts.get("villains")).toBe(3);
    expect(counts.get("allies")).toBe(0);
  });

  it("écrit le chemin d'une catégorie", () => {
    expect(categoryLabel(categories, "cult")).toBe("Antagonistes › Culte");
    expect(categoryLabel(categories, null)).toBe("");
  });
});
