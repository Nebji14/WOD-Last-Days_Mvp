/**
 * Lancer physique calculé d'avance, image par image.
 *
 * Chaque écran simule son propre lancer, puis tourne chaque dé visible d'une
 * symétrie du D10 pour que la face du dessus montre la valeur tirée par le
 * serveur. L'animation rejoue ensuite les images enregistrées.
 */
import {
  Body,
  ConvexPolyhedron,
  Material,
  Plane,
  Quaternion as CQuaternion,
  Vec3,
  World,
} from "cannon-es";
import { Quaternion, Vector3 } from "three";

import { DIE_SCALE, FACE_NORMALS, FACES, faceOf, symmetryBetween, VERTICES } from "./d10";

const STEP = 1 / 60;
const MAX_STEPS = 260;
const GRAVITY = -32;
/** Demi-largeur et demi-profondeur de la zone de lancer. */
export const ARENA = { x: 4.2, z: 2.6 };

export interface DieFrame {
  readonly position: Vector3;
  readonly quaternion: Quaternion;
}

export interface SimulatedDie {
  /** Pose du dé à chaque image. */
  readonly frames: readonly DieFrame[];
  /** Rotation à appliquer au dé visible pour montrer la valeur voulue. */
  readonly correction: Quaternion;
}

function wall(world: World, material: Material, normal: Vec3, offset: Vec3): void {
  const body = new Body({ mass: 0, material, shape: new Plane() });
  body.quaternion.setFromVectors(new Vec3(0, 0, 1), normal);
  body.position.copy(offset);
  world.addBody(body);
}

function dieShape(): ConvexPolyhedron {
  return new ConvexPolyhedron({
    vertices: VERTICES.map((v) => new Vec3(v.x * DIE_SCALE, v.y * DIE_SCALE, v.z * DIE_SCALE)),
    faces: FACES.map((face) => [...face]),
  });
}

/** Face tournée vers le haut, dans le repère du dé. */
function upFace(quaternion: CQuaternion): number {
  const rotation = new Quaternion(quaternion.x, quaternion.y, quaternion.z, quaternion.w);
  let best = 0;
  let bestHeight = -Infinity;
  FACE_NORMALS.forEach((normal, index) => {
    const height = normal.clone().applyQuaternion(rotation).y;
    if (height > bestHeight) {
      bestHeight = height;
      best = index;
    }
  });
  return best;
}

/**
 * Simule le lancer de dés qui doivent montrer `values`.
 *
 * @param random tirage entre 0 et 1, pour varier la trajectoire.
 */
export function simulateThrow(values: readonly number[], random: () => number): SimulatedDie[] {
  const world = new World({ gravity: new Vec3(0, GRAVITY, 0), allowSleep: true });
  const material = new Material("die");
  world.defaultContactMaterial.friction = 0.35;
  world.defaultContactMaterial.restitution = 0.35;
  wall(world, material, new Vec3(0, 1, 0), new Vec3(0, 0, 0));
  wall(world, material, new Vec3(-1, 0, 0), new Vec3(ARENA.x, 0, 0));
  wall(world, material, new Vec3(1, 0, 0), new Vec3(-ARENA.x, 0, 0));
  wall(world, material, new Vec3(0, 0, -1), new Vec3(0, 0, ARENA.z));
  wall(world, material, new Vec3(0, 0, 1), new Vec3(0, 0, -ARENA.z));

  const shape = dieShape();
  const bodies = values.map((_, index) => {
    const body = new Body({ mass: 1, material, shape, sleepSpeedLimit: 0.2, sleepTimeLimit: 0.25 });
    // Départ en grille, côté gauche, pour que les dés ne naissent pas l'un dans l'autre.
    const row = Math.floor(index / 5);
    const column = index % 5;
    body.position.set(-ARENA.x + 0.8 + row * 1.05, 2 + random() * 1.5, -2.1 + column * 1.05);
    body.velocity.set(9 + random() * 6, -2, (random() - 0.5) * 6);
    body.angularVelocity.set((random() - 0.5) * 30, (random() - 0.5) * 30, (random() - 0.5) * 30);
    body.quaternion.setFromEuler(random() * 6.3, random() * 6.3, random() * 6.3);
    world.addBody(body);
    return body;
  });

  const tracks = bodies.map((body) => ({ body, frames: [] as DieFrame[] }));
  for (let step = 0; step < MAX_STEPS; step += 1) {
    world.step(STEP);
    tracks.forEach(({ body, frames }) => {
      frames.push({
        position: new Vector3(body.position.x, body.position.y, body.position.z),
        quaternion: new Quaternion(
          body.quaternion.x,
          body.quaternion.y,
          body.quaternion.z,
          body.quaternion.w,
        ),
      });
    });
    if (step > 30 && bodies.every((body) => body.sleepState === Body.SLEEPING)) {
      break;
    }
  }

  return tracks.map(({ body, frames }, index) => ({
    frames,
    correction: symmetryBetween(faceOf(values[index] ?? 1), upFace(body.quaternion)),
  }));
}
