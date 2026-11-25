"use client";

/**
 * Images du MJ sur la table de jeu : pile à gauche du tapis et image affichée
 * en grand. Les actions du MJ (reposer, retirer) sont revérifiées par le serveur.
 */
import type { RealtimeClient } from "@/shared/realtime/client";

import { putDownImage, removeFromTable } from "../api";
import { useTableImages } from "../useTableImages";
import { ShownImageOverlay } from "./ShownImageOverlay";
import { TableImagePile } from "./TableImagePile";

interface TableImagesProps {
  readonly realtime: RealtimeClient | null;
  readonly isGm: boolean;
  readonly gmName: string;
}

/** Une action refusée laisse la scène inchangée ; la relecture suivante fait foi. */
function report(error: unknown): void {
  console.warn("Action sur les images de la table refusée", error);
}

export function TableImages({ realtime, isGm, gmName }: TableImagesProps) {
  const scene = useTableImages(realtime);

  return (
    <>
      <TableImagePile
        pile={scene.pile}
        isGm={isGm}
        paused={scene.shown !== null}
        onRemove={(imageId) => void removeFromTable(imageId).catch(report)}
      />
      {scene.shown !== null && (
        <ShownImageOverlay
          image={scene.shown}
          gmName={gmName}
          isGm={isGm}
          onPutDown={() => void putDownImage().catch(report)}
        />
      )}
    </>
  );
}
