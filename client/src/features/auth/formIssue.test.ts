import { describe, expect, it } from "vitest";

import { ApiError } from "@/shared/api/client";

import { findPasswordIssue, toIssue } from "./formIssue";

describe("refus d'un formulaire de compte", () => {
  it("garde le code et les règles connues de l'API", () => {
    const error = new ApiError(422, "password_too_weak", [{ rule: "digit" }, { rule: "autre" }]);
    expect(toIssue(error)).toEqual({ code: "password_too_weak", rules: ["digit"] });
  });

  it("ramène une erreur imprévue à une erreur interne", () => {
    expect(toIssue(new Error("x"))).toEqual({ code: "internal_error", rules: [] });
  });

  it("accepte un mot de passe conforme et confirmé", () => {
    expect(findPasswordIssue("chasseur-2026", "chasseur-2026")).toBeNull();
  });

  it("signale une confirmation différente", () => {
    expect(findPasswordIssue("chasseur-2026", "chasseur-2027")?.code).toBe("password_mismatch");
  });

  it("signale d'abord un mot de passe trop faible", () => {
    expect(findPasswordIssue("court", "autre")?.code).toBe("password_too_weak");
  });
});
