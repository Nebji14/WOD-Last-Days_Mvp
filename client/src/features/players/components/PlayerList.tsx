/**
 * Liste de tous les joueurs dans l'outil Joueurs : avatar, nom, personnages
 * (ou « Aucun personnage ») et présence. La ligne sélectionnée est bordée d'or.
 */
import { initials } from "@/features/table/seatLayout";
import { fill, labels } from "@/shared/i18n";

import type { Player } from "../api";
import { PresenceStatus } from "./PresenceStatus";

interface PlayerListProps {
  readonly players: readonly Player[];
  readonly selectedId: string | null;
  readonly onSelect: (playerId: string) => void;
}

export function PlayerList({ players, selectedId, onSelect }: PlayerListProps) {
  const text = labels.playersTool.list;
  const online = players.filter((player) => player.online).length;
  const count =
    players.length === 1
      ? fill(text.countOne, { online })
      : fill(text.count, { total: players.length, online });

  return (
    <section
      aria-label={text.title}
      className="border-line bg-panel flex min-h-0 flex-col rounded-xs border px-4 py-5"
    >
      <div className="mb-4 flex items-baseline justify-between px-1">
        <h2 className="font-display text-gold text-[12px] font-bold tracking-[3px]">
          {text.title}
        </h2>
        <span className="text-ink-muted text-sm italic">{count}</span>
      </div>
      {players.length === 0 && <p className="text-ink-faint px-1 text-lg italic">{text.empty}</p>}
      <ul className="flex min-h-0 flex-col gap-2 overflow-y-auto">
        {players.map((player) => {
          const selected = player.id === selectedId;
          return (
            <li key={player.id}>
              <button
                type="button"
                aria-pressed={selected}
                onClick={() => onSelect(player.id)}
                className={`flex h-[60px] w-full cursor-pointer items-center gap-3 rounded-xs border px-3 text-left transition-colors ${
                  selected ? "border-gold bg-[#1e1813]" : "border-line hover:border-line-strong"
                }`}
              >
                <span
                  aria-hidden="true"
                  className="border-line-strong bg-field font-display text-ink flex size-10 shrink-0 items-center justify-center rounded-full border-[1.5px] text-base font-bold"
                >
                  {initials(player.displayName).slice(0, 1)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="text-ink block truncate text-lg leading-6 font-bold">
                    {player.displayName}
                  </span>
                  <span className="text-ink-muted block truncate text-sm italic">
                    {player.characterNames.length === 0
                      ? text.noCharacter
                      : player.characterNames.join(", ")}
                  </span>
                </span>
                {player.status === "disabled" ? (
                  <span className="text-ink-faint text-sm italic">
                    {labels.playersTool.account.disabled}
                  </span>
                ) : (
                  <PresenceStatus online={player.online} />
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
