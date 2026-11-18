/**
 * Géométrie du dé à dix faces (trapézoèdre pentagonal) et ses symétries.
 *
 * Deux sommets aux pôles et dix sommets en zigzag autour de l'équateur forment
 * dix faces en cerf-volant. Les faces portent les valeurs 1 à 10. Les
 * symétries servent à tourner le dé visible sans changer sa forme, pour que la
 * face du dessus montre la valeur tirée par le serveur.
 */
import { BufferGeometry, Float32BufferAttribute, Quaternion, Vector3 } from "three";

const APEX = 1;
const RADIUS = 1;
const COS_36 = Math.cos(Math.PI / 5);
// Hauteur du zigzag qui rend chaque cerf-volant parfaitement plan.
const ZIGZAG = (APEX * (1 - COS_36)) / (1 + COS_36);
/** Taille du dé dans la scène. */
export const DIE_SCALE = 0.5;
// Côté du carré de texture posé sur une face, en unités du dé.
const UV_SPAN = 1.7;

export const FACE_COUNT = 10;

/** Face : pôle, sommet, pointe opposée au pôle, sommet. */
export type Face = readonly [number, number, number, number];

function ringVertex(index: number): Vector3 {
  const angle = (index * Math.PI) / 5;
  const height = index % 2 === 0 ? ZIGZAG : -ZIGZAG;
  return new Vector3(Math.cos(angle) * RADIUS, height, Math.sin(angle) * RADIUS);
}

/** Sommets du dé : 0 en haut, 1 en bas, puis l'anneau. */
export const VERTICES: readonly Vector3[] = [
  new Vector3(0, APEX, 0),
  new Vector3(0, -APEX, 0),
  ...Array.from({ length: 10 }, (_, index) => ringVertex(index)),
];

/** Lecture sûre d'un élément dont l'indice est garanti par construction. */
function at<T>(items: readonly T[], index: number): T {
  const item = items[index];
  if (item === undefined) {
    throw new RangeError(`indice ${index} hors du dé`);
  }
  return item;
}

function vertex(index: number): Vector3 {
  return at(VERTICES, index);
}

/** Les cinq premières faces entourent le pôle haut, les cinq suivantes le pôle bas. */
function rawFaces(): Face[] {
  const ring = (index: number) => 2 + (index % 10);
  const faces: Face[] = [];
  for (let i = 0; i < 5; i += 1) {
    faces.push([0, ring(2 * i), ring(2 * i + 1), ring(2 * i + 2)]);
  }
  for (let i = 0; i < 5; i += 1) {
    faces.push([1, ring(2 * i + 1), ring(2 * i + 2), ring(2 * i + 3)]);
  }
  return faces;
}

function normalOf(face: Face): Vector3 {
  const [a, b, c] = [vertex(face[0]), vertex(face[1]), vertex(face[2])];
  return new Vector3().subVectors(b, a).cross(new Vector3().subVectors(c, a)).normalize();
}

function centroidOf(face: Face): Vector3 {
  return face.reduce((sum, index) => sum.add(vertex(index)), new Vector3()).divideScalar(4);
}

/**
 * Faces orientées vers l'extérieur (sens trigonométrique vu de dehors), le
 * pôle toujours en premier et la pointe toujours en troisième.
 */
export const FACES: readonly Face[] = rawFaces().map(([pole, a, tip, b]): Face => {
  const face: Face = [pole, a, tip, b];
  return normalOf(face).dot(centroidOf(face)) > 0 ? face : [pole, b, tip, a];
});

export const FACE_NORMALS: readonly Vector3[] = FACES.map(normalOf);

/** Normale d'une face, dans le repère du dé. */
export function faceNormal(face: number): Vector3 {
  return at(FACE_NORMALS, face).clone();
}

/** Valeur portée par une face : impaires autour du pôle haut, paires autour du pôle bas. */
export function faceValue(face: number): number {
  return face < 5 ? 2 * face + 1 : 2 * (face - 5) + 2;
}

/** Face qui porte une valeur. */
export function faceOf(value: number): number {
  return value % 2 === 1 ? (value - 1) / 2 : 5 + (value - 2) / 2;
}

/** Sens de lecture du chiffre : de la pointe vers le pôle. */
export function faceUp(face: number): Vector3 {
  const [pole, , tip] = at(FACES, face);
  const normal = faceNormal(face);
  const up = new Vector3().subVectors(vertex(pole), vertex(tip));
  return up.sub(normal.multiplyScalar(up.dot(normal))).normalize();
}

/** Les dix rotations qui laissent le dé inchangé. */
const SYMMETRIES: readonly Quaternion[] = (() => {
  const vertical = new Vector3(0, 1, 0);
  const flipAxis = new Vector3(Math.cos(Math.PI / 10), 0, Math.sin(Math.PI / 10));
  const flip = new Quaternion().setFromAxisAngle(flipAxis, Math.PI);
  const turns = Array.from({ length: 5 }, (_, step) =>
    new Quaternion().setFromAxisAngle(vertical, (step * 2 * Math.PI) / 5),
  );
  return [...turns, ...turns.map((turn) => turn.clone().multiply(flip))];
})();

/** Rotation du dé visible qui amène la face `from` à la place de la face `to`. */
export function symmetryBetween(from: number, to: number): Quaternion {
  const target = faceNormal(to);
  const source = faceNormal(from);
  const found = SYMMETRIES.find(
    (rotation) => source.clone().applyQuaternion(rotation).dot(target) > 0.999,
  );
  return (found ?? new Quaternion()).clone();
}

/**
 * Coordonnées de texture des quatre coins d'une face (pôle, sommet, pointe,
 * sommet) : la texture est centrée sur la face, chiffre de la pointe vers le pôle.
 */
export function faceUvs(face: number): [number, number][] {
  const corners = at(FACES, face);
  const normal = faceNormal(face);
  const up = faceUp(face);
  const right = new Vector3().crossVectors(up, normal).normalize();
  const center = new Vector3()
    .addVectors(vertex(corners[0]), vertex(corners[2]))
    .multiplyScalar(0.5);
  return corners.map((index): [number, number] => {
    const offset = new Vector3().subVectors(vertex(index), center);
    return [0.5 + offset.dot(right) / UV_SPAN, 0.5 + offset.dot(up) / UV_SPAN];
  });
}

/** Géométrie affichable : deux triangles par face et un groupe de matériau par face. */
export function buildGeometry(): BufferGeometry {
  const positions: number[] = [];
  const normals: number[] = [];
  const uvs: number[] = [];
  const geometry = new BufferGeometry();
  FACES.forEach((face, faceIndex) => {
    const normal = faceNormal(faceIndex);
    const corners = faceUvs(faceIndex);
    [0, 1, 2, 0, 2, 3].forEach((corner) => {
      const point = vertex(at(face, corner));
      const [u, v] = at(corners, corner);
      positions.push(point.x * DIE_SCALE, point.y * DIE_SCALE, point.z * DIE_SCALE);
      normals.push(normal.x, normal.y, normal.z);
      uvs.push(u, v);
    });
    geometry.addGroup(faceIndex * 6, 6, faceIndex);
  });
  geometry.setAttribute("position", new Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new Float32BufferAttribute(normals, 3));
  geometry.setAttribute("uv", new Float32BufferAttribute(uvs, 2));
  return geometry;
}
