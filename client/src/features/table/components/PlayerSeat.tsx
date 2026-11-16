/**
 * Siège d'un joueur autour de la table ([Composant — Siège joueur]).
 *
 * - Mon siège : bordure or, [Étiquette — VOUS] et action principale
 *   ([Mon siège — Vous], [03 — Variante : Mon siège sans personnage]).
 * - Joueur déconnecté : siège atténué, pastille masquée (03-E2).
 * - Le siège apparaît en fondu à l'arrivée du joueur (03-A6).
 *
 * Un joueur ne peut rien faire sur le siège d'un autre (03-I7).
 */
import { labels } from "@/shared/i18n";

import type { PlacedSeat, SeatSlot } from "../seatLayout";

const SLOT_POSITION: Record<SeatSlot, string> = {
  "left-1": "left-10 top-[196px]",
  "left-2": "left-10 top-[340px]",
  "left-3": "left-10 top-[484px]",
  "right-1": "right-10 top-[196px]",
  "right-2": "right-10 top-[340px]",
  "right-3": "right-10 top-[484px]",
  "bottom-left": "bottom-5 left-[calc(50%-395px)]",
  "bottom-center": "bottom-5 left-[calc(50%-125px)]",
  "bottom-right": "bottom-5 left-[calc(50%+145px)]",
};

export function PlayerSeat({ slot, seat, mine }: PlacedSeat) {
  const text = labels.table.seat;
  const frame = mine
    ? "border-gold border-[1.5px] shadow-[0_0_22px_rgb(201_176_106/0.25),0_10px_24px_rgb(0_0_0/0.67)] min-h-[128px]"
    : "border-line border shadow-seat min-h-[124px]";

  return (
    <section
      aria-label={seat.displayName}
      className={`bg-seat animate-seat-in absolute z-10 w-[250px] rounded-md transition-opacity duration-500 ${frame} ${SLOT_POSITION[slot]} ${
        seat.online ? "" : "opacity-55"
      }`}
    >
      <span
        aria-hidden="true"
        className="border-line-strong bg-field font-display text-ink absolute top-3.5 left-3.5 flex size-11 items-center justify-center rounded-full border-[1.5px] text-[15px] font-bold"
      >
        ?
      </span>
      {seat.online && (
        <span
          aria-hidden="true"
          className="bg-online absolute top-[47px] left-[47px] size-[11px] rounded-full border-2 border-[#110e0c]"
        />
      )}
      <p className="text-ink-muted absolute top-[11px] right-16 left-[70px] truncate text-sm leading-[17px] font-medium italic">
        {seat.displayName}
      </p>
      <p className="text-ink absolute top-[26px] left-[70px] text-xl leading-6 font-bold">
        {text.noCharacter}
      </p>
      {mine && (
        <>
          <p className="text-ink-muted absolute top-[50px] left-[70px] text-[13px] leading-4 italic">
            {text.createHint}
          </p>
          <span className="bg-gold font-display absolute top-3 right-[7px] flex h-[18px] items-center rounded-xs px-[7px] text-[9px] font-bold tracking-[2px] text-[#120c0a]">
            {text.you}
          </span>
          {/* TODO(US-007, 03-I2) : ouvrir la création de personnage (écran 06) en fenêtre détachable. */}
          <button
            type="button"
            disabled
            title={labels.table.comingSoon}
            className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright absolute top-[82px] left-3.5 h-8 w-[222px] cursor-not-allowed rounded-xs border bg-linear-to-b text-[11px] font-bold tracking-[2px] opacity-60"
          >
            {text.createCharacter}
          </button>
        </>
      )}
    </section>
  );
}
