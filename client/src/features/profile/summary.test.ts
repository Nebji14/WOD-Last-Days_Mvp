import { describe, expect, it } from "vitest";

import type { Character, Sheet } from "@/features/characters/model";

import { formsSummary, playedFirst } from "./summary";

/** Personnage réduit aux champs lus par les résumés du profil. */
function character(id: string, isPlayed: boolean, forms: readonly [boolean, string][]): Character {
  const sheets = forms.map(([isMain, formName]) => ({ is_main: isMain, form_name: formName }));
  return { id, is_played: isPlayed, sheets: sheets as unknown as Sheet[] } as unknown as Character;
}

describe("09 · résumé des formes", () => {
  it("nomme « principale » la seule forme d'un personnage", () => {
    expect(formsSummary(character("a", false, [[true, "Forme principale"]]))).toBe(
      "1 forme : principale",
    );
  });

  it("place la forme principale en premier et compte toutes les formes", () => {
    const werewolf = character("a", false, [
      [false, "Loup-garou"],
      [true, "Forme principale"],
    ]);
    expect(formsSummary(werewolf)).toBe("2 formes : principale, Loup-garou");
  });
});

describe("09 · ordre des cartes", () => {
  it("met le personnage à la table en premier sans changer l'ordre des autres", () => {
    const list = [character("a", false, []), character("b", false, []), character("c", true, [])];
    expect(playedFirst(list).map((item) => item.id)).toEqual(["c", "a", "b"]);
  });
});
