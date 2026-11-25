/**
 * Panneau « Mes personnages » du profil : le personnage joué en premier, puis
 * les autres. « Créer un personnage » ouvre l'assistant dans sa fenêtre.
 */
import type { Character } from "@/features/characters/model";
import { errorLabel, fill, labels } from "@/shared/i18n";
import { openCreation } from "@/shared/windows/detached";

import { playedFirst } from "../summary";
import { CharacterCard } from "./CharacterCard";
import type { PortraitActions } from "./CharacterPortraits";

interface CharactersPanelProps extends PortraitActions {
  readonly characters: readonly Character[];
  readonly busyId: string | null;
  readonly errorCode: string | null;
  readonly onPlay: (characterId: string) => void;
  readonly onDelete: (characterId: string) => void;
}

export function CharactersPanel(props: CharactersPanelProps) {
  const { characters, busyId, errorCode, onPlay, onDelete, onPortrait, onRemovePortrait } = props;
  const text = labels.profile.characters;

  return (
    <section
      aria-label={fill(text.title, { count: characters.length })}
      className="border-line bg-panel flex min-h-0 flex-col rounded-xs border px-6 py-4"
    >
      <div className="mb-5 flex items-center justify-between">
        <h2 className="font-display text-copper-light text-[12px] font-bold tracking-[3px]">
          {fill(text.title, { count: characters.length })}
        </h2>
        <button
          type="button"
          onClick={openCreation}
          className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright h-[38px] cursor-pointer rounded-xs border bg-linear-to-b px-3 text-[12px] font-bold tracking-[2px] shadow-[0_0_16px_rgb(216_53_44/0.33)] hover:brightness-110"
        >
          {text.create}
        </button>
      </div>

      {errorCode !== null && (
        <p role="alert" className="text-danger mb-3 text-[15px]">
          {errorLabel(errorCode)}
        </p>
      )}

      {characters.length === 0 ? (
        <p className="text-ink-faint text-lg italic">{text.empty}</p>
      ) : (
        <ul className="flex min-h-0 flex-col gap-4 overflow-y-auto pr-1">
          {playedFirst(characters).map((character) => (
            <CharacterCard
              key={character.id}
              character={character}
              busy={busyId === character.id}
              onPlay={() => onPlay(character.id)}
              onDelete={() => onDelete(character.id)}
              onPortrait={onPortrait}
              onRemovePortrait={onRemovePortrait}
            />
          ))}
        </ul>
      )}

      <p className="text-ink-faint mt-auto pt-4 text-[15px] italic">{text.deleteHint}</p>
    </section>
  );
}
