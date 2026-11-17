import { describe, expect, it } from "vitest";

import { FACE_COUNT, faceNormal, faceOf, faceValue, symmetryBetween } from "./d10";

const faces = Array.from({ length: FACE_COUNT }, (_, index) => index);

describe("dé à dix faces", () => {
  it("porte chaque valeur de 1 à 10 une seule fois", () => {
    expect(faces.map(faceValue).sort((a, b) => a - b)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    expect(faces.every((face) => faceOf(faceValue(face)) === face)).toBe(true);
  });

  it("amène n'importe quelle face à la place de n'importe quelle autre", () => {
    for (const from of faces) {
      for (const to of faces) {
        const moved = faceNormal(from).applyQuaternion(symmetryBetween(from, to));
        expect(moved.dot(faceNormal(to))).toBeGreaterThan(0.999);
      }
    }
  });
});
