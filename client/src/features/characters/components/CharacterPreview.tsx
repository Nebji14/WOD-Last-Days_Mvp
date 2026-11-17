/**
 * [Aperçu du personnage (siège)] : le personnage tel qu'il apparaît sur un siège
 * de la table (instance du [Composant — Siège joueur]).
 *
 * Utilisé par les cartes du profil (09) et par l'outil Joueurs du MJ (04a).
 */
import { type Character, mainSheet } from "@/features/characters/model";
import { initials } from "@/features/table/seatLayout";
import { labels } from "@/shared/i18n";
import { HealthTrack, WillpowerDots } from "@/shared/ui/Gauges";

const GAUGE_LABEL = "font-display text-ink-muted w-16 text-[9px] font-bold tracking-[2px]";

interface CharacterPreviewProps {
  readonly character: Character;
  /** Le propriétaire est connecté : pastille verte sur l'avatar. */
  readonly online: boolean;
}

export function CharacterPreview({ character, online }: CharacterPreviewProps) {
  const text = labels.table.seat;
  const sheet = mainSheet(character);
  const name = sheet.texts.name ?? "";

  return (
    <div className="border-line bg-seat flex w-[250px] shrink-0 flex-col gap-2 rounded-md border p-3.5">
      <div className="flex items-center gap-3">
        <span
          aria-hidden="true"
          className="border-line-strong bg-field font-display text-ink relative flex size-11 shrink-0 items-center justify-center rounded-full border-[1.5px] text-[15px] font-bold"
        >
          {initials(name)}
          {online && (
            <span className="bg-online absolute -right-0.5 -bottom-0.5 size-[11px] rounded-full border-2 border-[#110e0c]" />
          )}
        </span>
        <div className="min-w-0">
          <p className="text-ink-muted truncate text-sm italic">{character.owner_name}</p>
          <p className="text-ink truncate text-xl leading-6 font-bold">{name}</p>
          <p className="text-ink-muted truncate text-[13px] italic">{sheet.texts.concept}</p>
        </div>
      </div>
      <div className="mt-1 flex items-center">
        <span className={GAUGE_LABEL}>{text.health}</span>
        <HealthTrack
          capacity={sheet.effective.health_max}
          wounds={sheet.wound_track}
          label={text.health}
        />
      </div>
      <div className="flex items-center">
        <span className={GAUGE_LABEL}>{text.willpower}</span>
        <WillpowerDots
          max={sheet.effective.willpower_max}
          current={sheet.willpower_current}
          label={text.willpower}
        />
      </div>
    </div>
  );
}
