import { describe, expect, it } from "vitest";

import { parseGoogleResult } from "./googleResult";

describe("résultat du retour de Google", () => {
  it.each(["linked", "confirmed"] as const)("reconnaît le succès %s", (value) => {
    expect(parseGoogleResult(value)).toEqual({ kind: value });
  });

  it("reprend une erreur attendue", () => {
    expect(parseGoogleResult("google_already_linked")).toEqual({
      kind: "error",
      code: "google_already_linked",
    });
  });

  it("ignore une valeur absente, inconnue ou répétée", () => {
    expect(parseGoogleResult(undefined)).toBeNull();
    expect(parseGoogleResult("<script>")).toBeNull();
    expect(parseGoogleResult(["linked", "linked"])).toBeNull();
  });
});
