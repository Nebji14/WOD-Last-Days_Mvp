import { describe, expect, it } from "vitest";

import { arrangeSeats, initials } from "./seatLayout";
import type { Seat } from "./state";

function seat(position: number, accountId: string): Seat {
  return { position, accountId, displayName: accountId, online: true, character: null };
}

describe("arrangeSeats", () => {
  it("place mon siège en bas au centre et les autres sur les côtés (vue joueur)", () => {
    const placed = arrangeSeats([seat(0, "lea"), seat(1, "moi"), seat(2, "ben")], "moi");

    expect(placed.map((p) => [p.seat.accountId, p.slot, p.mine])).toEqual([
      ["lea", "left-1", false],
      ["moi", "bottom-center", true],
      ["ben", "right-1", false],
    ]);
  });

  it("traite le bas au centre comme une place ordinaire en vue MJ (03-MJ-D3)", () => {
    const seats = Array.from({ length: 9 }, (_, index) => seat(index, `j${index}`));

    const placed = arrangeSeats(seats, null);

    expect(placed.map((p) => p.slot)).toEqual([
      "left-1",
      "right-1",
      "left-2",
      "right-2",
      "left-3",
      "right-3",
      "bottom-center",
      "bottom-left",
      "bottom-right",
    ]);
    expect(placed.every((p) => !p.mine)).toBe(true);
  });

  it("remplit les huit emplacements restants en vue joueur avec neuf joueurs", () => {
    const seats = Array.from({ length: 9 }, (_, index) => seat(index, `j${index}`));

    const placed = arrangeSeats(seats, "j4");

    expect(placed).toHaveLength(9);
    expect(new Set(placed.map((p) => p.slot)).size).toBe(9);
    expect(placed.find((p) => p.mine)?.slot).toBe("bottom-center");
  });

  it("suit l'ordre des places du serveur, quel que soit l'ordre de réception", () => {
    const placed = arrangeSeats([seat(3, "c"), seat(0, "a"), seat(1, "b")], null);

    expect(placed.map((p) => p.seat.accountId)).toEqual(["a", "b", "c"]);
  });

  it("garde son emplacement à un joueur quand un autre se déconnecte (Q03-7)", () => {
    const before = arrangeSeats([seat(0, "lea"), seat(1, "ben"), seat(2, "moi")], "moi");
    const after = arrangeSeats(
      [{ ...seat(0, "lea"), online: false }, seat(1, "ben"), seat(2, "moi")],
      "moi",
    );

    expect(after.map((p) => p.slot)).toEqual(before.map((p) => p.slot));
  });
});

describe("initials", () => {
  it("prend la première lettre des deux premiers mots", () => {
    expect(initials("lea.vale")).toBe("LV");
    expect(initials("Marcus Vale")).toBe("MV");
  });

  it("prend les deux premières lettres d'un nom en un seul mot", () => {
    expect(initials("axel")).toBe("AX");
  });
});
