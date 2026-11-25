import { describe, expect, it } from "vitest";

import { isValidUsername, normalizedDisplayName, passwordViolations } from "./validation";

describe("isValidUsername", () => {
  it.each(["lea", "lea.vale", "Yanis_42", "a-b-c", "x".repeat(24)])("accepte %s", (username) => {
    expect(isValidUsername(username)).toBe(true);
  });

  it.each(["", "ab", "x".repeat(25), "léa", "lea vale", "lea@vale"])("refuse %s", (username) => {
    expect(isValidUsername(username)).toBe(false);
  });
});

describe("normalizedDisplayName", () => {
  it.each([
    ["Léa", "Léa"],
    ["  Léa   la  Chasseuse ", "Léa la Chasseuse"],
    ["x".repeat(40), "x".repeat(40)],
  ])("accepte %s", (name, expected) => {
    expect(normalizedDisplayName(name)).toBe(expected);
  });

  it.each(["", "   ", "x".repeat(41), "Lé\u200ba", "Léa\u0000"])("refuse %j", (name) => {
    expect(normalizedDisplayName(name)).toBeNull();
  });
});

describe("passwordViolations", () => {
  it("ne signale rien pour un mot de passe conforme", () => {
    expect(passwordViolations("chasseur-2026")).toEqual([]);
  });

  it.each([
    ["court1abc", "min_length"],
    ["1234567890", "letter"],
    ["sanschiffre", "digit"],
    ["a1" + "x".repeat(71), "max_length"],
    ["é".repeat(36) + "a1", "max_length"],
  ] as const)("signale la règle manquante pour %s", (password, rule) => {
    expect(passwordViolations(password)).toContain(rule);
  });
});
