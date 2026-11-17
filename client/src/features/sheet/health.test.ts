import { describe, expect, it } from "vitest";

import { boxPenalty, healthState, woundPenalty } from "./health";

describe("malus de blessure", () => {
  it("marque −1, −2 et −3 sur les trois dernières cases", () => {
    expect([0, 3, 4, 5, 6].map((index) => boxPenalty(index, 7))).toEqual([0, 0, -1, -2, -3]);
  });

  it("prend le malus de la case blessée la plus à droite, sans cumul", () => {
    expect(woundPenalty("", 7)).toBe(0);
    expect(woundPenalty("X//", 7)).toBe(0);
    expect(woundPenalty("XX///", 7)).toBe(-1);
    expect(woundPenalty("*XXXXX/", 7)).toBe(-3);
  });
});

describe("état critique", () => {
  it("reste normal tant qu'une case est vide", () => {
    expect(healthState("XXXXXX", 7)).toBe("fine");
  });

  it("dépend de la dernière case quand la piste est pleine", () => {
    expect(healthState("XXX////", 7)).toBe("unconscious");
    expect(healthState("*XXXXXX", 7)).toBe("bleeding");
    expect(healthState("*******", 7)).toBe("dead");
  });
});
