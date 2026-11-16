"use client";

/**
 * Scène à l'échelle de la fenêtre.
 *
 * Les écrans de jeu sont dessinés pour 1440 × 900 (maquette). La scène garde
 * ces proportions : elle est agrandie ou réduite d'un seul bloc pour remplir
 * la fenêtre, et l'espace restant en largeur ou en hauteur lui est ajouté.
 * Son contenu se positionne donc en pixels de maquette.
 *
 * L'échelle est appliquée par le DOM et non par un attribut `style` : la
 * politique de sécurité du contenu interdit les styles en ligne.
 */
import { type ReactNode, useLayoutEffect, useRef } from "react";

const DESIGN_WIDTH = 1440;
const DESIGN_HEIGHT = 900;
const MIN_SCALE = 0.6;
const MAX_SCALE = 1.6;

interface ScaledStageProps {
  readonly children: ReactNode;
}

export function ScaledStage({ children }: ScaledStageProps) {
  const frameRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const frame = frameRef.current;
    const stage = stageRef.current;
    if (!frame || !stage) {
      return;
    }
    const fit = (): void => {
      const { clientWidth, clientHeight } = frame;
      const ratio = Math.min(clientWidth / DESIGN_WIDTH, clientHeight / DESIGN_HEIGHT);
      const scale = Math.min(Math.max(ratio, MIN_SCALE), MAX_SCALE);
      stage.style.width = `${Math.max(clientWidth / scale, DESIGN_WIDTH)}px`;
      stage.style.height = `${Math.max(clientHeight / scale, DESIGN_HEIGHT)}px`;
      stage.style.transform = `scale(${scale})`;
      stage.dataset.ready = "true";
    };
    const observer = new ResizeObserver(fit);
    observer.observe(frame);
    fit();
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={frameRef} className="bg-night fixed inset-0 overflow-auto">
      <div
        ref={stageRef}
        className="absolute top-0 left-0 origin-top-left opacity-0 data-[ready=true]:opacity-100"
      >
        {children}
      </div>
    </div>
  );
}
