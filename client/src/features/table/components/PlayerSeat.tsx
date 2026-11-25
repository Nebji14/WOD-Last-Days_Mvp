"use client";

/**
 * Siège d'un joueur autour de la table.
 *
 * - Personnage joué : portrait ou initiales, nom, concept, santé et volonté, visibles de
 *   tous ; sinon « Aucun personnage ».
 * - Mon siège : bordure or, étiquette « VOUS » et bouton « Ouvrir ma fiche » ou
 *   « Créer mon personnage ».
 * - Le MJ n'ouvre pas les fiches depuis les sièges : il passe par l'outil Joueurs.
 * - Joueur déconnecté : siège atténué. Le siège apparaît en fondu à l'arrivée.
 */
import { Portrait } from "@/features/characters/components/Portrait";
import { labels } from "@/shared/i18n";
import { HealthTrack, WillpowerDots } from "@/shared/ui/Gauges";
import { openCreation, openSheet } from "@/shared/windows/detached";

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

const MAIN_ACTION =
  "from-blood-from to-blood-to border-blood-line font-display text-ink-bright absolute left-3.5 h-8 w-[222px] cursor-pointer rounded-xs border bg-linear-to-b text-[11px] font-bold tracking-[2px] shadow-[0_0_12px_rgb(216_53_44/0.33)] transition hover:brightness-110";
const GAUGE_LABEL =
  "font-display text-ink-muted absolute left-3.5 text-[9px] leading-3 font-bold tracking-[2px]";

export function PlayerSeat({ slot, seat, mine }: PlacedSeat) {
  const text = labels.table.seat;
  const { character } = seat;
  const height = mine ? (character ? "h-[168px]" : "h-[128px]") : "h-[124px]";
  const frame = mine
    ? "border-gold border-[1.5px] shadow-[0_0_22px_rgb(201_176_106/0.25),0_10px_24px_rgb(0_0_0/0.67)]"
    : "border-line border shadow-seat";

  return (
    <section
      aria-label={seat.displayName}
      className={`bg-seat animate-seat-in absolute z-10 w-[250px] rounded-md transition-opacity duration-500 ${height} ${frame} ${SLOT_POSITION[slot]} ${
        seat.online ? "" : "opacity-55"
      }`}
    >
      <Portrait
        portrait={character?.portrait ?? null}
        name={character ? character.name : "?"}
        className="absolute top-3.5 left-3.5 size-11 text-[15px]"
      />
      {seat.online && (
        <span
          aria-hidden="true"
          className="bg-online absolute top-[47px] left-[47px] size-[11px] rounded-full border-2 border-[#110e0c]"
        />
      )}
      <p className="text-ink-muted absolute top-[11px] right-16 left-[70px] truncate text-sm leading-[17px] font-medium italic">
        {seat.displayName}
      </p>
      <p className="text-ink absolute top-[26px] right-2 left-[70px] truncate text-xl leading-6 font-bold">
        {character ? character.name : text.noCharacter}
      </p>
      <p className="text-ink-muted absolute top-[50px] right-2 left-[70px] truncate text-[13px] leading-4 italic">
        {character ? character.concept : mine ? text.createHint : ""}
      </p>
      {mine && (
        <span className="bg-gold font-display absolute top-3 right-[7px] flex h-[18px] items-center rounded-xs px-[7px] text-[9px] font-bold tracking-[2px] text-[#120c0a]">
          {text.you}
        </span>
      )}

      {character && (
        <>
          <span className={`${GAUGE_LABEL} top-[78px]`}>{text.health}</span>
          <span className="absolute top-[77px] left-20">
            <HealthTrack
              capacity={character.healthMax}
              wounds={character.woundTrack}
              label={text.health}
            />
          </span>
          <span className={`${GAUGE_LABEL} top-[98px]`}>{text.willpower}</span>
          <span className="absolute top-[98px] left-20">
            <WillpowerDots
              max={character.willpowerMax}
              current={character.willpowerCurrent}
              label={text.willpower}
            />
          </span>
        </>
      )}

      {mine && character && (
        <button
          type="button"
          onClick={() => openSheet(character.id)}
          className={`${MAIN_ACTION} top-[124px]`}
        >
          {text.openSheet}
        </button>
      )}
      {mine && !character && (
        <button type="button" onClick={openCreation} className={`${MAIN_ACTION} top-[82px]`}>
          {text.createCharacter}
        </button>
      )}
    </section>
  );
}
