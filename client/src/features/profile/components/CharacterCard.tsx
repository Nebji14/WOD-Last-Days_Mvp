"use client";

/**
 * Carte « Personnage — … » du profil (09).
 *
 * À gauche, le personnage tel qu'il apparaît sur un siège de la table ; à
 * droite, ses formes et ses actions :
 * - I1 [Bouton — Ouvrir la fiche] → fiche (05) en fenêtre détachée ;
 * - I3 [Lien — Supprimer le personnage] → confirmation qui rappelle son nom,
 *   suppression définitive (US-010, Q09-2) ;
 * - I4 [Bouton — Jouer ce personnage] → il prend place sur le siège du joueur,
 *   choix libre (Q09-1). Le personnage joué porte [Étiquette — À la table].
 */
import { useState } from "react";

import { CharacterPreview } from "@/features/characters/components/CharacterPreview";
import { type Character, mainSheet } from "@/features/characters/model";
import { fill, labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";
import { openSheet } from "@/shared/windows/detached";

import { formsSummary } from "../summary";

const TAG = "font-display h-6 rounded-xs px-2.5 text-[10px] font-bold tracking-[2px]";

interface CharacterCardProps {
  readonly character: Character;
  /** Une action sur ce personnage est en cours. */
  readonly busy: boolean;
  readonly onPlay: () => void;
  readonly onDelete: () => void;
}

export function CharacterCard({ character, busy, onPlay, onDelete }: CharacterCardProps) {
  const text = labels.profile.characters;
  const [confirming, setConfirming] = useState(false);
  const name = mainSheet(character).texts.name ?? "";

  return (
    <li
      aria-label={name}
      className={`bg-field-deep flex gap-7 rounded-xs border p-3 ${
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
        <div className="flex items-center justify-between gap-4">
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
