/**
 * Carte d'un PNJ dans la liste : photo modifiable, nom, modèle, concept et résumé chiffré
 * (santé et volonté, plus Puissance, Finesse et Résilience pour un PNJ
 * simplifié), avec « Ouvrir la fiche » et « Supprimer ».
 */
import { useState } from "react";

import { PortraitPicker } from "@/features/characters/components/PortraitPicker";
import { removePortrait, setPortrait } from "@/features/characters/portrait";
import { fill, labels } from "@/shared/i18n";
import { openSheet } from "@/shared/windows/detached";

import type { NpcCard } from "../api";

interface NpcCardItemProps {
  readonly npc: NpcCard;
  /** Lance une action, signale son éventuel échec, puis relit la liste. */
  readonly act: (action: () => Promise<unknown>) => Promise<boolean>;
  readonly onDelete: () => void;
}

export function NpcCardItem({ npc, act, onDelete }: NpcCardItemProps) {
  const text = labels.npcsTool;
  const [sending, setSending] = useState(false);

  function run(action: () => Promise<unknown>): void {
    setSending(true);
    void act(action).finally(() => setSending(false));
  }

  const summary =
    npc.model === "simplified"
      ? fill(text.simplifiedSummary, {
          power: npc.power ?? 1,
          finesse: npc.finesse ?? 1,
          resilience: npc.resilience ?? 1,
          health: npc.healthMax,
          willpower: npc.willpowerMax,
        })
      : fill(text.fullSummary, { health: npc.healthMax, willpower: npc.willpowerMax });

  return (
    <li className="border-line flex flex-col gap-2.5 rounded-xs border px-4 py-3.5">
      <div className="flex items-start gap-4">
        <PortraitPicker
          portrait={npc.portrait}
          name={npc.name}
          className="size-16 text-[19px]"
          busy={sending}
          compact
          onSave={(files) => run(() => setPortrait(npc.sheetId, files))}
          onRemove={() => run(() => removePortrait(npc.sheetId))}
        />
        <div className="flex min-w-0 flex-1 flex-col gap-2.5">
          <p className="text-ink-bright truncate text-2xl font-bold">{npc.name}</p>
          <span className="border-gold font-display text-gold self-start rounded-xs border px-2 py-0.5 text-[9px] font-bold tracking-[2px]">
            {text.badge[npc.model]}
          </span>
          <p className="text-ink-muted truncate text-[17px] italic">{npc.concept}</p>
        </div>
      </div>
      <p className="text-ink text-[17px]">{summary}</p>
      <div className="mt-1 flex items-center gap-6">
        <button
          type="button"
          onClick={() => openSheet(npc.id)}
          className="border-line-strong font-display text-ink hover:border-gold h-9 cursor-pointer rounded-xs border px-6 text-[11px] font-bold tracking-[2.5px] transition-colors"
        >
          {text.open}
        </button>
        <button
          type="button"
          aria-label={fill(text.deleteNpcLabel, { name: npc.name })}
          onClick={onDelete}
          className="font-display text-danger cursor-pointer text-[11px] font-bold tracking-[2px] hover:brightness-125"
        >
          {text.deleteNpc}
        </button>
      </div>
    </li>
  );
}
