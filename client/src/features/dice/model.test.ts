import { describe, expect, it } from "vitest";

import { doubledLabel } from "./format";
import { isDoubled, isReroll, type Roll } from "./model";

const base = {
  kind: "pool",
  chance: false,
  again: 10,
  specialty: false,
  doubled: 0,
} as unknown as Roll;

describe("jet sous spécialité", () => {
  it("compte double les dés au seuil au lieu de les relancer", () => {
    const roll = { ...base, specialty: true, again: 9 };
    expect(isDoubled(9, roll)).toBe(true);
    expect(isDoubled(8, roll)).toBe(false);
    expect(isReroll(10, roll)).toBe(false);
  });

  it("relance les 10 sans spécialité", () => {
    expect(isDoubled(10, base)).toBe(false);
    expect(isReroll(10, base)).toBe(true);
  });

  it("ne double jamais un dé de chance", () => {
    expect(isDoubled(10, { ...base, specialty: true, chance: true })).toBe(false);
  });

  it("annonce le nombre de dés doublés", () => {
    expect(doubledLabel(base)).toBeNull();
    expect(doubledLabel({ ...base, doubled: 1 })).toBe("dont 1 dé compté double");
    expect(doubledLabel({ ...base, doubled: 3 })).toBe("dont 3 dés comptés double");
  });
});
