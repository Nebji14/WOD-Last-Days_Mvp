import { describe, expect, it } from "vitest";

import { parseTableState } from "./state";

const seat = { position: 0, account_id: "a1", display_name: "lea.vale", online: true };

describe("parseTableState", () => {
  it("convertit un état valide", () => {
    const state = parseTableState({
      gm: { display_name: "conteur", online: false },
      seats: [seat],
    });

    expect(state).toEqual({
      gm: { displayName: "conteur", online: false },
      seats: [{ position: 0, accountId: "a1", displayName: "lea.vale", online: true }],
    });
  });

  it("accepte un MJ dont le compte n'existe pas encore", () => {
    expect(parseTableState({ gm: { display_name: null, online: false }, seats: [] })).toEqual({
      gm: { displayName: null, online: false },
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
