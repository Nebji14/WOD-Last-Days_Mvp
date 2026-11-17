import { describe, expect, it } from "vitest";

import { googleReturnError } from "./googleReturn";

describe("erreur au retour de Google", () => {
  it("ne signale rien sans paramètre d'erreur", () => {
    expect(googleReturnError({})).toBeNull();
  });

  it("reprend un code attendu", () => {
    expect(googleReturnError({ erreur: "google_failed" })?.code).toBe("google_failed");
  });

  it("ignore un code inconnu", () => {
    expect(googleReturnError({ erreur: "<script>" })).toBeNull();
  });

  it("donne au MJ le lien vers sa page", () => {
    const error = googleReturnError({ erreur: "wrong_portal_gm", acces: "/mj-dev" });
    expect(error?.details).toEqual([{ gm_access_path: "/mj-dev" }]);
  });

  it("refuse un lien vers une autre adresse", () => {
    const error = googleReturnError({ erreur: "wrong_portal_gm", acces: "//exemple.com" });
    expect(error?.details).toEqual([]);
  });
});
