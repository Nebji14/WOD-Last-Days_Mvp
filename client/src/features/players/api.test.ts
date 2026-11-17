import { describe, expect, it } from "vitest";

import { ApiError } from "@/shared/api/client";

import { parsePlayer } from "./api";

const VALID = {
  id: "3f1c",
  username: "lea.vale",
  display_name: "Léa",
  status: "active",
  online: true,
  character_names: ["Marcus Vale"],
};

describe("lecture d'un joueur", () => {
  it("convertit la réponse du serveur", () => {
    expect(parsePlayer(VALID)).toEqual({
      id: "3f1c",
      username: "lea.vale",
      displayName: "Léa",
      status: "active",
      online: true,
      characterNames: ["Marcus Vale"],
    });
  });

  it("accepte un joueur sans personnage", () => {
    expect(parsePlayer({ ...VALID, character_names: [] }).characterNames).toEqual([]);
  });

  it("refuse une réponse mal formée", () => {
    expect(() => parsePlayer({ ...VALID, status: "unknown" })).toThrow(ApiError);
    expect(() => parsePlayer({ ...VALID, character_names: [1] })).toThrow(ApiError);
  });
});
