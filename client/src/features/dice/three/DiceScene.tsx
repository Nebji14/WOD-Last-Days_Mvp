"use client";

/**
 * Scène 3D des dés : le lancer roule sur la table, puis les dés viennent en
 * gros plan au centre, face tirée vers l'écran, réussites en lumière.
 */
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import { type Camera, type Mesh, Quaternion, Vector3 } from "three";

import { buildGeometry, faceNormal, faceOf, faceUp } from "./d10";
import { type DieStyle, faceMaterials, highlightedMaterials } from "./materials";
import { simulateThrow } from "./simulate";

const PLAYBACK_FPS = 60;
const SETTLE_HOLD_SECONDS = 0.5;
const CLOSEUP_DISTANCE = 5.2;
const CLOSEUP_GROW_SECONDS = 0.45;
const MAX_COLUMNS = 8;
const CAMERA_POSITION: [number, number, number] = [0, 9, 6.5];

export interface ThrowSpec {
  readonly key: string;
  readonly values: readonly number[];
  readonly style: DieStyle;
}

export interface CloseupDie {
  readonly value: number;
  readonly success: boolean;
  /** Dé de la dernière vague : il arrive en grandissant. */
  readonly fresh: boolean;
}

export interface CloseupSpec {
  readonly key: string;
  readonly dice: readonly CloseupDie[];
  readonly style: DieStyle;
}

interface DiceSceneProps {
  readonly throwSpec: ThrowSpec | null;
  readonly closeup: CloseupSpec | null;
  readonly onThrowEnd: (key: string) => void;
}

/** Hasard reproductible : le même jet roule de la même façon sur tous les écrans. */
function seededRandom(seed: string): () => number {
  let state = [...seed].reduce(
    (hash, char) => Math.imul(hash ^ char.charCodeAt(0), 16777619),
    2166136261,
  );
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let value = Math.imul(state ^ (state >>> 15), 1 | state);
    value = (value + Math.imul(value ^ (value >>> 7), 61 | value)) ^ value;
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

const geometry = buildGeometry();

function ThrownDice({ spec, onEnd }: { spec: ThrowSpec; onEnd: (key: string) => void }) {
  const dice = useMemo(() => simulateThrow(spec.values, seededRandom(spec.key)), [spec]);
  const meshes = useRef<(Mesh | null)[]>([]);
  const elapsed = useRef(0);
  const ended = useRef(false);
  const length = Math.max(...dice.map((die) => die.frames.length));

  useFrame((_, delta) => {
    elapsed.current += delta;
    const frame = Math.min(Math.floor(elapsed.current * PLAYBACK_FPS), length - 1);
    dice.forEach((die, index) => {
      const mesh = meshes.current[index];
      const pose = die.frames[Math.min(frame, die.frames.length - 1)];
      if (mesh !== null && mesh !== undefined && pose !== undefined) {
        mesh.position.copy(pose.position);
        mesh.quaternion.copy(pose.quaternion).multiply(die.correction);
      }
    });
    if (!ended.current && elapsed.current > length / PLAYBACK_FPS + SETTLE_HOLD_SECONDS) {
      ended.current = true;
      onEnd(spec.key);
    }
  });

  const materials = [...faceMaterials(spec.style)];
  return (
    <>
      {dice.map((_, index) => (
        <mesh
          key={index}
          ref={(mesh) => {
            meshes.current[index] = mesh;
          }}
          geometry={geometry}
          material={materials}
          castShadow
        />
      ))}
    </>
  );
}

/** Orientation qui montre la valeur à la caméra, chiffre à l'endroit. */
function facingCamera(value: number, toCamera: Vector3, cameraUp: Vector3): Quaternion {
  const face = faceOf(value);
  const turn = new Quaternion().setFromUnitVectors(faceNormal(face), toCamera);
  const up = faceUp(face).applyQuaternion(turn);
  const wanted = cameraUp.clone().sub(toCamera.clone().multiplyScalar(cameraUp.dot(toCamera)));
  const angle = Math.atan2(new Vector3().crossVectors(up, wanted).dot(toCamera), up.dot(wanted));
  return new Quaternion().setFromAxisAngle(toCamera, angle).multiply(turn);
}

function closeupLayout(count: number, camera: Camera) {
  const columns = Math.min(count, MAX_COLUMNS);
  const rows = Math.ceil(count / columns);
  const spacing = Math.min(1.3, 6.4 / columns, 3.2 / rows);
  const forward = new Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  const right = new Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  const up = new Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
  const center = camera.position.clone().add(forward.clone().multiplyScalar(CLOSEUP_DISTANCE));
  center.add(up.clone().multiplyScalar(0.35));
  return Array.from({ length: count }, (_, index) => {
    const row = Math.floor(index / columns);
    const inRow = row === rows - 1 ? count - row * columns : columns;
    const column = index % columns;
    const position = center
      .clone()
      .add(right.clone().multiplyScalar((column - (inRow - 1) / 2) * spacing))
      .add(up.clone().multiplyScalar(((rows - 1) / 2 - row) * spacing));
    const toCamera = camera.position.clone().sub(position).normalize();
    return { position, toCamera, up, scale: spacing / 1.3 };
  });
}

function CloseupDice({ spec }: { spec: CloseupSpec }) {
  const camera = useThree((state) => state.camera);
  const layout = useMemo(() => closeupLayout(spec.dice.length, camera), [spec, camera]);
  const materials = useMemo(
    () => spec.dice.map((die) => highlightedMaterials(spec.style, die.success)),
    [spec],
  );
  const meshes = useRef<(Mesh | null)[]>([]);
  const elapsed = useRef(0);

  useEffect(
    () => () => materials.forEach((set) => set.forEach((material) => material.dispose())),
    [materials],
  );

  useFrame((_, delta) => {
    elapsed.current += delta;
    const grow = Math.min(1, elapsed.current / CLOSEUP_GROW_SECONDS);
    const eased = 1 - (1 - grow) ** 3;
    spec.dice.forEach((die, index) => {
      const mesh = meshes.current[index];
      const slot = layout[index];
      if (mesh === null || mesh === undefined || slot === undefined) {
        return;
      }
      const bob = die.success ? Math.sin(elapsed.current * 3 + index) * 0.04 : 0;
      mesh.position.copy(slot.position).add(slot.up.clone().multiplyScalar(bob));
      mesh.quaternion.copy(facingCamera(die.value, slot.toCamera, slot.up));
      const size = slot.scale * (die.fresh ? eased : 1) * (die.success ? 1.08 : 0.92);
      mesh.scale.setScalar(Math.max(size, 0.001));
    });
  });

  return (
    <>
      {spec.dice.map((_, index) => (
        <mesh
          key={index}
          ref={(mesh) => {
            meshes.current[index] = mesh;
          }}
          geometry={geometry}
          material={materials[index]}
        />
      ))}
    </>
  );
}

export default function DiceScene({ throwSpec, closeup, onThrowEnd }: DiceSceneProps) {
  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      gl={{ alpha: true, antialias: true }}
      camera={{ position: CAMERA_POSITION, fov: 40 }}
      onCreated={({ camera }) => camera.lookAt(0, 0, 0)}
    >
      <ambientLight intensity={0.7} />
      <directionalLight position={[3, 10, 4]} intensity={2.2} castShadow />
      <pointLight position={[-4, 4, 3]} intensity={18} color="#e6b493" />
      <mesh rotation-x={-Math.PI / 2} receiveShadow>
        <planeGeometry args={[20, 20]} />
        <shadowMaterial opacity={0.45} />
      </mesh>
      {closeup === null && throwSpec !== null && (
        <ThrownDice key={throwSpec.key} spec={throwSpec} onEnd={onThrowEnd} />
      )}
      {closeup !== null && <CloseupDice key={closeup.key} spec={closeup} />}
    </Canvas>
  );
}
