"use client";

/**
 * Médaillon d'un personnage : son portrait, ou ses initiales tant qu'il n'en a
 * pas. Décoratif : le nom est toujours écrit à côté.
 */
import { initials } from "@/features/table/seatLayout";

import { usePortraitUrl } from "../usePortraitUrl";

interface PortraitProps {
  /** Nom du fichier du portrait, `null` sans image. */
  readonly portrait: string | null;
  /** Nom du personnage, pour les initiales. */
  readonly name: string;
  /** Taille et taille de texte du médaillon. */
  readonly className: string;
}

export function Portrait({ portrait, name, className }: PortraitProps) {
  const url = usePortraitUrl(portrait);

  return (
    <span
      aria-hidden="true"
      className={`border-line-strong bg-field font-display text-ink flex shrink-0 items-center justify-center overflow-hidden rounded-full border-[1.5px] font-bold ${className}`}
    >
      {url === null ? (
        initials(name)
      ) : (
        // eslint-disable-next-line @next/next/no-img-element -- image locale déjà réduite
        <img src={url} alt="" draggable={false} className="size-full object-cover" />
      )}
    </span>
  );
}
