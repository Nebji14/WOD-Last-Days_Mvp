/**
 * [Outils MJ (icônes)] de l'en-tête (03-MJ-D1) : Joueurs, Images, PNJ.
 *
 * Ce composant n'est rendu que pour le compte MJ ; les droits sont de toute
 * façon contrôlés par le serveur à chaque appel (03-MJ-D6).
 */
import type { ReactNode } from "react";

import { labels } from "@/shared/i18n";
import { openPlayersTool } from "@/shared/windows/detached";

interface ToolProps {
  readonly label: string;
  readonly hint: string;
  /** Ouvre la fenêtre détachée de l'outil ; absent tant que l'outil n'existe pas. */
  readonly onOpen?: () => void;
  readonly children: ReactNode;
}

// TODO(US-031, US-040) : ouvrir la fenêtre détachable des outils Images et PNJ (04b, 04c).
function Tool({ label, hint, onOpen, children }: ToolProps) {
  const ready = onOpen !== undefined;
  return (
    <button
      type="button"
      disabled={!ready}
      onClick={onOpen}
      title={ready ? hint : `${hint} — ${labels.table.comingSoon}`}
      className="border-line bg-panel hover:border-gold disabled:hover:border-line flex h-[52px] w-16 cursor-pointer flex-col items-center gap-[5px] rounded-sm border pt-2 transition-colors disabled:cursor-not-allowed disabled:opacity-60"
    >
      <svg
        viewBox="0 0 24 20"
        aria-hidden="true"
        className="text-ink h-5 w-6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        {children}
      </svg>
      <span className="font-display text-ink-muted text-[8px] leading-[11px] font-bold tracking-[1.5px]">
        {label}
      </span>
    </button>
  );
}

export function GmTools() {
  const text = labels.table.tools;

  return (
    <nav className="absolute top-1.5 left-1/2 flex -translate-x-1/2 gap-2">
      <Tool label={text.players} hint={text.playersHint} onOpen={openPlayersTool}>
        <circle cx="7.5" cy="4.5" r="3.5" />
        <path d="M1 19c0-3.5 2.9-6 6.5-6s6.5 2.5 6.5 6" />
        <circle cx="18" cy="6" r="3" className="text-ink-muted" stroke="currentColor" />
        <path d="M16 12c3.6-.6 7 1.6 7 6" className="text-ink-muted" stroke="currentColor" />
      </Tool>
      <Tool label={text.images} hint={text.imagesHint}>
        <rect x="1" y="2" width="22" height="16" rx="1.5" />
        <path d="M4 15l5-6 4 4 3-3 4 5" />
        <circle
          cx="16.75"
          cy="6.75"
          r="1.75"
          className="text-gold"
          fill="currentColor"
          stroke="none"
        />
      </Tool>
      <Tool label={text.npcs} hint={text.npcsHint}>
        <rect x="5" y="0.75" width="15" height="18.5" rx="1.5" />
        <circle cx="12.5" cy="5.5" r="2.5" strokeWidth="1.3" />
        <path d="M8.5 12.5c0-1.7 1.8-2.6 4-2.6s4 .9 4 2.6" strokeWidth="1.3" />
        <path d="M8.5 16.2h8" className="text-gold" stroke="currentColor" strokeWidth="1.3" />
      </Tool>
    </nav>
  );
}
