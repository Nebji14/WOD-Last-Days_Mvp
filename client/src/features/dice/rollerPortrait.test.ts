import { describe, expect, it } from "vitest";

import type { Seat, SeatCharacter } from "@/features/table/state";

import type { Roll } from "./model";
import { rollerPortrait } from "./rollerPortrait";

function seat(characterId: string, portrait: string | null): Seat {
  const character = { id: characterId, name: "Isaac", portrait } as SeatCharacter;
  return { position: 0, accountId: "a1", displayName: "lea", online: true, character };
}

function roll(characterId: string | null, role: "player" | "gm" = "player"): Roll {
  return { id: "r1", character_id: characterId, roller_role: role } as Roll;
}

const empty: Seat = { ...seat("c0", null), character: null };
const seats = [empty, seat("c1", "un.webp"), seat("c2", null)];

describe("photo du lanceur", () => {
  it("prend la photo du personnage sur son siège", () => {
    expect(rollerPortrait(roll("c1"), seats, "mj.webp")).toBe("un.webp");
  });

  it("ne montre rien pour un personnage sans photo", () => {
    expect(rollerPortrait(roll("c2"), seats, "mj.webp")).toBeNull();
  });

  it("ne montre rien pour un personnage absent de la table", () => {
    expect(rollerPortrait(roll("autre"), seats, "mj.webp")).toBeNull();
  });

  it("montre la photo du MJ pour un jet libre ou un PNJ", () => {
    expect(rollerPortrait(roll(null, "gm"), seats, "mj.webp")).toBe("mj.webp");
    expect(rollerPortrait(roll("pnj", "gm"), seats, "mj.webp")).toBe("mj.webp");
    expect(rollerPortrait(roll(null, "gm"), seats, null)).toBeNull();
  });

  it("montre le personnage quand le MJ lance pour un joueur", () => {
    expect(rollerPortrait(roll("c1", "gm"), seats, "mj.webp")).toBe("un.webp");
  });
});
