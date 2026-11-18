import { describe, expect, it } from "vitest";

import { draftOf, recipeOf } from "./components/RecipeEditor";

describe("recette de jet et ressource libre", () => {
  it("garde la ressource choisie et son coût", () => {
    const draft = { ...draftOf(null), parts: ["wits"], resource_id: "mana", resource_cost: 2 };
    expect(recipeOf(draft)).toMatchObject({ resource_id: "mana", resource_cost: 2 });
  });

  it("n'enregistre aucune ressource sans coût ou sans ressource choisie", () => {
    const base = { ...draftOf(null), parts: ["wits"] };
    expect(recipeOf({ ...base, resource_id: "mana", resource_cost: 0 })).toMatchObject({
      resource_id: null,
      resource_cost: 0,
    });
    expect(recipeOf({ ...base, resource_id: "", resource_cost: 2 })).toMatchObject({
      resource_id: null,
      resource_cost: 0,
    });
  });

  it("relit une ancienne recette sans ressource", () => {
    const draft = draftOf({ parts: ["wits"], willpower_cost: 1, bonus: 0 });
    expect(draft.resource_id).toBe("");
    expect(draft.resource_cost).toBe(0);
  });
});
