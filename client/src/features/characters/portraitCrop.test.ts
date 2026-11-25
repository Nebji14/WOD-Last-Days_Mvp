import { describe, expect, it } from "vitest";

import { initialCrop, MAX_ZOOM, moveCrop, zoomCrop, zoomOf } from "./portraitCrop";

const wide = { width: 1000, height: 400 };
const tall = { width: 400, height: 1000 };

describe("cadrage d'un portrait", () => {
  it("garde une image carrée entière", () => {
    expect(initialCrop({ width: 400, height: 400 })).toEqual({ x: 0, y: 0, side: 400 });
  });

  it("centre au départ une image en largeur", () => {
    expect(initialCrop(wide)).toEqual({ x: 300, y: 0, side: 400 });
  });

  it("propose plutôt le haut d'une image en hauteur", () => {
    expect(initialCrop(tall)).toEqual({ x: 0, y: 150, side: 400 });
  });

  it("déplace le cadre", () => {
    expect(moveCrop(initialCrop(wide), -100, 0, wide)).toEqual({ x: 200, y: 0, side: 400 });
  });

  it("ne sort jamais de l'image", () => {
    expect(moveCrop(initialCrop(wide), 5000, 5000, wide)).toEqual({ x: 600, y: 0, side: 400 });
    expect(moveCrop(initialCrop(wide), -5000, -5000, wide)).toEqual({ x: 0, y: 0, side: 400 });
  });

  it("zoome autour du centre du cadre", () => {
    expect(zoomCrop(initialCrop(wide), 2, wide)).toEqual({ x: 400, y: 100, side: 200 });
  });

  it("borne le zoom", () => {
    expect(zoomOf(zoomCrop(initialCrop(tall), 50, tall), tall)).toBe(MAX_ZOOM);
    expect(zoomOf(zoomCrop(initialCrop(tall), 0.1, tall), tall)).toBe(1);
  });

  it("reste dans l'image quand on dézoome depuis un bord", () => {
    const corner = moveCrop(zoomCrop(initialCrop(wide), 2, wide), 5000, 5000, wide);

    expect(zoomCrop(corner, 1, wide)).toEqual({ x: 600, y: 0, side: 400 });
  });
});
