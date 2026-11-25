/**
 * Détail du joueur sélectionné dans l'outil Joueurs.
 *
 * Données du compte, puis pour chaque personnage : aperçu, « Consulter la
 * fiche », « Modifier la fiche » et bloc Éveil. Les notes du joueur se lisent
 * depuis sa fiche.
 */
import { CharacterPreview } from "@/features/characters/components/CharacterPreview";
import type { Character } from "@/features/characters/model";
import { initials } from "@/features/table/seatLayout";
import { fill, labels } from "@/shared/i18n";
import { openSheet } from "@/shared/windows/detached";

import type { Player } from "../api";
import { AwakeningBlock } from "./AwakeningBlock";
import { PresenceStatus } from "./PresenceStatus";

const SECTION_TITLE = "font-display text-gold text-[11px] font-bold tracking-[3px]";
const SHEET_BUTTON =
  "font-display h-10 w-[330px] cursor-pointer rounded-xs border text-[12px] font-bold tracking-[2.5px]";

interface PlayerDetailProps {
  readonly player: Player;
  readonly characters: readonly Character[];
  readonly busyId: string | null;
  readonly onAwaken: (characterId: string) => void;
  readonly onReactivate: () => void;
}

export function PlayerDetail(props: PlayerDetailProps) {
  const { player, characters, busyId, onAwaken, onReactivate } = props;
  const text = labels.playersTool;

  return (
    <section
      aria-label={player.displayName}
      className="border-line bg-panel flex min-h-0 flex-col rounded-xs border px-6 py-6"
    >
      <div className="flex items-center gap-5">
        <span
          aria-hidden="true"
          className="border-gold bg-field font-display text-ink-bright flex size-[72px] shrink-0 items-center justify-center rounded-full border-2 text-3xl font-bold"
        >
          {initials(player.displayName).slice(0, 1)}
        </span>
        <div>
          <h2 className="text-ink-bright text-3xl font-bold">{player.displayName}</h2>
          <PresenceStatus online={player.online} onlineText={text.onlineAtTable} />
        </div>
      </div>

      <h3 className={`${SECTION_TITLE} mt-7 mb-3`}>{text.account.title}</h3>
      <dl className="border-line-soft grid grid-cols-[196px_1fr] gap-y-1.5 border-b pb-4 text-[17px]">
        <dt className="text-ink-muted">{text.account.username}</dt>
        <dd className="text-ink">{player.username}</dd>
        <dt className="text-ink-muted">{text.account.methods}</dt>
        <dd className="text-ink">{text.account.methodsValue}</dd>
        <dt className="text-ink-muted">{text.account.state}</dt>
        <dd className="text-ink flex flex-wrap items-center gap-4">
          {player.status === "active" ? text.account.active : text.account.disabled}
          {player.status === "disabled" && (
            <button
              type="button"
              onClick={onReactivate}
              disabled={busyId === player.id}
              className="border-gold font-display text-gold hover:bg-gold hover:text-abyss min-h-9 cursor-pointer rounded-xs border px-4 text-[11px] font-bold tracking-[2px] transition-colors disabled:cursor-wait disabled:opacity-60"
            >
              {text.account.reactivate}
            </button>
          )}
        </dd>
      </dl>

      <h3 className={`${SECTION_TITLE} mt-5 mb-3`}>
        {fill(text.characters.title, { count: characters.length })}
      </h3>
      {characters.length === 0 ? (
        <p className="text-ink-faint text-lg italic">{text.characters.none}</p>
      ) : (
        <ul className="flex min-h-0 flex-col gap-4 overflow-y-auto pr-1">
          {characters.map((character) => (
            <li key={character.id} className="flex flex-col gap-3">
              <div className="border-line flex items-center gap-7 rounded-xs border p-3">
                <CharacterPreview character={character} online={player.online} />
                <div className="flex flex-col gap-2.5">
                  <button
                    type="button"
                    onClick={() => openSheet(character.id)}
                    className={`${SHEET_BUTTON} border-line-strong text-ink hover:border-gold`}
                  >
                    {text.characters.consult}
                  </button>
                  <button
                    type="button"
                    onClick={() => openSheet(character.id, true)}
                    className={`${SHEET_BUTTON} from-blood-from to-blood-to border-blood-line text-ink-bright bg-linear-to-b shadow-[0_0_16px_rgb(216_53_44/0.33)] hover:brightness-110`}
                  >
                    {text.characters.edit}
                  </button>
                </div>
              </div>
              <AwakeningBlock
                character={character}
                busy={busyId === character.id}
                onAwaken={() => onAwaken(character.id)}
              />
            </li>
          ))}
        </ul>
      )}

      <p className="text-ink-faint mt-auto pt-4 text-[15px] italic">{text.hint}</p>
    </section>
  );
}
