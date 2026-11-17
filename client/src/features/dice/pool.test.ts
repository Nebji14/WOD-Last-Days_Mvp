import { describe, expect, it } from "vitest";

import type { Character, Sheet } from "@/features/characters/model";

import { EMPTY_CHOICE, pickTrait, previewParts } from "./pool";

const sheet = {
  attributes: { strength: 3, dexterity: 2, wits: 2, resolve: 2, composure: 3 },
  skills: { brawl: 2, academics: 0, stealth: 0 },
  specialties: { brawl: ["Prises"] },
  wound_track: "",
  effective: { health_max: 7 },
} as unknown as Sheet;
const character = { npc: null } as unknown as Character;

describe("aperçu de la réserve", () => {
  it("additionne attribut, compétence, spécialité, volonté et malus du MJ", () => {
    const choice = {
      ...EMPTY_CHOICE,
      attribute: "strength",
      second: "brawl",
      specialty: true,
      willpower: true,
      modifier: -2,
    } as const;
    expect(previewParts(character, sheet, choice)).toEqual([
      { key: "strength", value: 3 },
      { key: "brawl", value: 2 },
      { key: "specialty", value: 1 },
      { key: "willpower", value: 3 },
      { key: "modifier", value: -2 },
    ]);
  });

  it("applique le malus de compétence à 0 selon sa catégorie", () => {
    const mental = previewParts(character, sheet, {
      ...EMPTY_CHOICE,
      attribute: "wits",
      second: "academics",
    });
    expect(mental).toContainEqual({ key: "unskilled", value: -3 });
  });

  it("ajoute le malus de blessure des dernières cases", () => {
    const wounded = { ...sheet, wound_track: "XXXXXX" } as Sheet;
    const parts = previewParts(character, wounded, { ...EMPTY_CHOICE, attribute: "strength" });
    expect(parts).toContainEqual({ key: "wounds", value: -2 });
  });
});

describe("sélection sur la fiche", () => {
  it("prend un attribut puis une compétence, et retire un trait recliqué", () => {
    let choice = pickTrait(EMPTY_CHOICE, "strength");
    choice = pickTrait(choice, "brawl");
    expect([choice.attribute, choice.second]).toEqual(["strength", "brawl"]);
    expect(pickTrait(choice, "brawl").second).toBeNull();
  });

  it("accepte deux attributs", () => {
    const choice = pickTrait(pickTrait(EMPTY_CHOICE, "resolve"), "composure");
    expect([choice.attribute, choice.second]).toEqual(["resolve", "composure"]);
  });
});
