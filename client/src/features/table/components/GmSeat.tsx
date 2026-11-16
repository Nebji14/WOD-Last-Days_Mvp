/**
 * [Siège — Maître du jeu (informatif)] : nom du MJ, présence et nombre de
 * joueurs connectés (US-012 · CA2). Aucune action.
 *
 * En vue MJ, le siège porte [Étiquette — VOUS] et une bordure cuivre renforcée
 * (03-MJ-D2).
 */
import { labels } from "@/shared/i18n";

import type { TableState } from "../state";

interface GmSeatProps {
  readonly gm: TableState["gm"];
  readonly onlinePlayers: number;
  readonly isViewer: boolean;
}

function playersLabel(count: number): string {
  const text = labels.table.gm;
  if (count === 0) {
    return text.noPlayer;
  }
  return count === 1 ? text.onePlayer : text.manyPlayers.replace("{count}", String(count));
}

export function GmSeat({ gm, onlinePlayers, isViewer }: GmSeatProps) {
  const text = labels.table.gm;

  return (
    <section
      className={`absolute top-[86px] left-1/2 z-10 h-[104px] w-[380px] -translate-x-1/2 rounded-md bg-[rgb(18_12_10/0.95)] shadow-[0_0_28px_rgb(183_119_77/0.2),0_10px_24px_rgb(0_0_0/0.67)] ${
        isViewer ? "border-copper border-[1.5px]" : "border-copper-to border"
      }`}
    >
      <span
        aria-hidden="true"
        className="border-copper font-display text-ink-bright absolute top-[18px] left-[18px] flex size-[68px] items-center justify-center rounded-full border-2 bg-[radial-gradient(circle,#322218_0%,#130d09_100%)] text-2xl font-black shadow-[0_0_14px_rgb(183_119_77/0.4)]"
      >
        {text.initials}
      </span>
      <p className="font-display text-copper absolute top-5 left-[104px] text-[10px] leading-[13px] font-bold tracking-[3px]">
        {text.title}
      </p>
      <p className="text-ink-bright absolute top-[34px] right-4 left-[104px] truncate text-[28px] leading-[34px] font-bold">
        {gm.displayName ?? text.unknownName}
      </p>
      <p className="text-ink-muted absolute top-[70px] left-[105px] flex items-center gap-[7px] text-[15px] leading-[18px] font-medium italic">
        <span
          aria-hidden="true"
          className={`size-2 rounded-full ${gm.online ? "bg-online" : "bg-ink-faint"}`}
        />
        {gm.online ? text.online : text.offline} · {playersLabel(onlinePlayers)}
      </p>
      {isViewer && (
        <span className="bg-copper font-display text-ink-bright absolute top-3 right-[11px] flex h-[18px] items-center rounded-xs px-[7px] text-[9px] font-bold tracking-[2px]">
          {labels.table.seat.you}
        </span>
      )}
    </section>
  );
}
