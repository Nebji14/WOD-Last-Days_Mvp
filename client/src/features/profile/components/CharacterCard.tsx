"use client";

/**
 * Carte d'un personnage dans le profil.
 *
 * À gauche, l'aperçu du personnage ; à droite, ses formes et ses actions :
 * ouvrir la fiche, le jouer à la table, ou le supprimer définitivement après une
 * confirmation qui rappelle son nom. Le personnage joué porte « À la table ».
 */
import { useState } from "react";

import { CharacterPreview } from "@/features/characters/components/CharacterPreview";
import { type Character, mainSheet } from "@/features/characters/model";
import { fill, labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";
import { openSheet } from "@/shared/windows/detached";

import { formsSummary } from "../summary";
import { CharacterPortraits, type PortraitActions } from "./CharacterPortraits";

const TAG = "font-display h-6 rounded-xs px-2.5 text-[10px] font-bold tracking-[2px]";

interface CharacterCardProps extends PortraitActions {
  readonly character: Character;
  /** Une action sur ce personnage est en cours. */
  readonly busy: boolean;
  readonly onPlay: () => void;
  readonly onDelete: () => void;
}

export function CharacterCard(props: CharacterCardProps) {
  const { character, busy, onPlay, onDelete, onPortrait, onRemovePortrait } = props;
  const text = labels.profile.characters;
  const [confirming, setConfirming] = useState(false);
  const name = mainSheet(character).texts.name ?? "";

  return (
    <li
      aria-label={name}
      className={`bg-field-deep flex flex-col gap-4 rounded-xs border p-3 sm:flex-row sm:gap-7 ${
        character.is_played ? "border-gold shadow-[0_0_18px_rgb(201_176_106/0.15)]" : "border-line"
      }`}
    >
      <CharacterPreview character={character} online />

      <div className="flex flex-1 flex-col justify-between py-1.5 pr-4">
        <div className="flex flex-col items-start gap-2.5">
          {character.is_played ? (
            <span className={`${TAG} bg-gold flex items-center text-[#120c0a]`}>
              {text.atTable}
            </span>
          ) : (
            <button
              type="button"
              onClick={onPlay}
              disabled={busy}
              className={`${TAG} border-gold text-gold cursor-pointer border hover:brightness-125 disabled:cursor-wait disabled:opacity-60`}
            >
              {text.play}
            </button>
          )}
          <p className="text-ink-muted text-base italic">{formsSummary(character)}</p>
        </div>
        <CharacterPortraits
          character={character}
          busy={busy}
          onPortrait={onPortrait}
          onRemovePortrait={onRemovePortrait}
        />
        <div className="flex flex-wrap items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => openSheet(character.id)}
            className="border-line-strong font-display text-ink hover:border-gold h-10 w-[200px] cursor-pointer rounded-xs border text-[12px] font-bold tracking-[2.5px] transition-colors"
          >
            {text.open}
          </button>
          <button
            type="button"
            onClick={() => setConfirming(true)}
            disabled={busy}
            aria-label={fill(text.deleteLabel, { name })}
            className="font-display text-danger cursor-pointer text-[11px] font-bold tracking-[2px] hover:brightness-125 disabled:cursor-wait disabled:opacity-60"
          >
            {text.delete}
          </button>
        </div>
      </div>

      <ConfirmDialog
        open={confirming}
        title={text.deleteTitle}
        question={fill(text.deleteQuestion, { name })}
        confirmLabel={text.delete}
        cancelLabel={labels.sheet.cancel}
        onConfirm={() => {
          setConfirming(false);
          onDelete();
        }}
        onCancel={() => setConfirming(false)}
      />
    </li>
  );
}
