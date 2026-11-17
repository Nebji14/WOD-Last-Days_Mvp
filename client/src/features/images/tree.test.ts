import { describe, expect, it } from "vitest";

import type { ImageFolder, LibraryImage } from "./api";
import { childrenOf, folderPath, imageCounts, imagesIn, isWithin, searchImages } from "./tree";

const folders: ImageFolder[] = [
  { id: "docks", name: "Les docks", parentId: null },
  { id: "places", name: "Lieux", parentId: "docks" },
  { id: "clues", name: "Indices", parentId: "docks" },
  { id: "maps", name: "Cartes", parentId: null },
];

function image(id: string, name: string, folderId: string | null): LibraryImage {
  return { id, name, folderId, url: null, isShown: false, onTable: false };
}

const images = [
  image("quay", "Quai de nuit", "places"),
  image("symbol", "Symbole du culte", "clues"),
  image("manor", "Plan du manoir", "maps"),
  image("loose", "Ruelle", null),
];

describe("arborescence des dossiers", () => {
  it("liste les sous-dossiers d'un dossier par nom", () => {
    expect(childrenOf(folders, "docks").map((f) => f.id)).toEqual(["clues", "places"]);
    expect(childrenOf(folders, null).map((f) => f.id)).toEqual(["maps", "docks"]);
  });

  it("montre seulement les images du dossier ouvert, toutes à la racine", () => {
    expect(imagesIn(images, "docks")).toEqual([]);
    expect(imagesIn(images, "places").map((i) => i.id)).toEqual(["quay"]);
    expect(imagesIn(images, null)).toHaveLength(4);
  });

  it("compte les images rangées directement dans chaque dossier", () => {
    expect(imageCounts(images).get("places")).toBe(1);
    expect(imageCounts(images).get("docks")).toBeUndefined();
  });

  it("donne le chemin d'un dossier et détecte un rangement en cycle", () => {
    expect(folderPath(folders, "places").map((f) => f.name)).toEqual(["Les docks", "Lieux"]);
    expect(isWithin(folders, "docks", "places")).toBe(true);
    expect(isWithin(folders, "places", "maps")).toBe(false);
  });
});

describe("recherche d'images", () => {
  it("cherche dans le nom des images et des dossiers, sans casse ni accents", () => {
    expect(searchImages(images, folders, "symbole").map((i) => i.id)).toEqual(["symbol"]);
    expect(searchImages(images, folders, "DOCKS").map((i) => i.id)).toEqual(["quay", "symbol"]);
    expect(searchImages(images, folders, "lieux").map((i) => i.id)).toEqual(["quay"]);
    expect(searchImages(images, folders, "   ")).toEqual([]);
  });
});
