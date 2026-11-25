import { describe, expect, it } from "vitest";

import { parseTableState } from "./state";

const seat = {
  position: 0,
  account_id: "a1",
  display_name: "lea.vale",
  online: true,
  character: null,
};
const character = {
  id: "c1",
  name: "Isaac Thorne",
  concept: "Chasseur de primes",
  health_max: 7,
  wound_track: "*X/",
  willpower_max: 4,
  willpower_current: 2,
  portrait: "abc.webp",
};

describe("parseTableState", () => {
  it("convertit un état valide", () => {
    const state = parseTableState({
      gm: { display_name: "conteur", online: false, portrait: "mj.webp" },
      seats: [seat],
    });

    expect(state).toEqual({
      gm: { displayName: "conteur", online: false, portrait: "mj.webp" },
      seats: [
        { position: 0, accountId: "a1", displayName: "lea.vale", online: true, character: null },
      ],
    });
  });

  it("convertit le personnage joué d'un siège", () => {
    const state = parseTableState({
      gm: { display_name: null, online: false },
      seats: [{ ...seat, character }],
    });

    expect(state?.seats[0]?.character).toEqual({
      id: "c1",
      name: "Isaac Thorne",
      concept: "Chasseur de primes",
      healthMax: 7,
      woundTrack: "*X/",
      willpowerMax: 4,
      willpowerCurrent: 2,
      portrait: "abc.webp",
    });
  });

  it("affiche un personnage sans portrait", () => {
    const state = parseTableState({
      gm: { display_name: null, online: false },
      seats: [{ ...seat, character: { ...character, portrait: null } }],
    });

    expect(state?.seats[0]?.character?.portrait).toBeNull();
  });

  it("rejette un siège dont le personnage est mal formé", () => {
    const broken = { ...seat, character: { ...character, health_max: "7" } };

    expect(
      parseTableState({ gm: { display_name: null, online: false }, seats: [broken] }),
    ).toBeNull();
  });

  it("accepte un MJ dont le compte n'existe pas encore", () => {
    expect(parseTableState({ gm: { display_name: null, online: false }, seats: [] })).toEqual({
      gm: { displayName: null, online: false, portrait: null },
      seats: [],
    });
  });

  it("rejette un état mal formé", () => {
    expect(parseTableState(null)).toBeNull();
    expect(parseTableState({ gm: { display_name: "x" }, seats: [] })).toBeNull();
    expect(
      parseTableState({ gm: { display_name: "x", online: true }, seats: [{ ...seat, online: 1 }] }),
    ).toBeNull();
  });
});
