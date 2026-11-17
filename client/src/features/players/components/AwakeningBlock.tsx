"use client";

/**
 * [Éveil du personnage (visible par le MJ uniquement)] (04a, notes 05 ÉVEIL).
 *
 * Cadre en pointillés : élément réservé au MJ. [Bouton — Déclencher l'éveil]
 * demande une confirmation (04a-I5), puis disparaît : l'éveil n'est pas
 * réversible au MVP (Q05-13).
 */
import { useState } from "react";

import { type Character, mainSheet } from "@/features/characters/model";
import { longDate } from "@/shared/format/date";
import { fill, labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";

interface AwakeningBlockProps {
  readonly character: Character;
  readonly busy: boolean;
  readonly onAwaken: () => void;
}

export function AwakeningBlock({ character, busy, onAwaken }: AwakeningBlockProps) {
  const text = labels.playersTool.awakening;
  const [confirming, setConfirming] = useState(false);
  const name = mainSheet(character).texts.name ?? "";
  const awakenedAt = character.awakened_at ?? null;

  return (
    <div className="border-line-strong flex items-center justify-between gap-6 rounded-xs border border-dashed px-5 py-4">
      <div>
        <p className="font-display text-gold text-[10px] font-bold tracking-[2px]">{text.title}</p>
        <p className="text-ink mt-2 text-base italic">
          {awakenedAt === null
            ? fill(text.dormant, { name })
            : fill(text.awakened, { name, date: longDate(new Date(awakenedAt)) })}
        </p>
      </div>
      {awakenedAt === null && (
        <button
          type="button"
          onClick={() => setConfirming(true)}
          disabled={busy}
          className="border-copper font-display text-copper-light h-9 shrink-0 cursor-pointer rounded-xs border px-3.5 text-[11px] font-bold tracking-[2px] hover:brightness-125 disabled:cursor-wait disabled:opacity-60"
        >
          {text.trigger}
        </button>
      )}
      <ConfirmDialog
        open={confirming}
        title={text.confirmTitle}
        question={fill(text.confirmQuestion, { name })}
        confirmLabel={text.confirm}
        cancelLabel={text.cancel}
        onConfirm={() => {
          setConfirming(false);
          onAwaken();
        }}
        onCancel={() => setConfirming(false)}
      />
    </div>
  );
}
