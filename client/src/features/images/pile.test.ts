import { describe, expect, it } from "vitest";

import type { LibraryImage } from "./api";
import { neighbour } from "./pile";

const pile = ["a", "b", "c"].map((id) => ({ id }) as LibraryImage);

describe("parcours des images de la table", () => {
  it("passe à la suivante et à la précédente", () => {
    expect(neighbour(pile, "a", 1)?.id).toBe("b");
    expect(neighbour(pile, "c", -1)?.id).toBe("b");
  });

  it("repart de l'autre bout", () => {
    expect(neighbour(pile, "c", 1)?.id).toBe("a");
    expect(neighbour(pile, "a", -1)?.id).toBe("c");
  });

  it("ne trouve rien pour une image retirée de la table", () => {
    expect(neighbour(pile, "x", 1)).toBeNull();
    expect(neighbour([], "a", 1)).toBeNull();
  });
});
