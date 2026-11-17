/**
 * Carte d'un PNJ dans la liste : nom, modèle, concept et résumé chiffré
 * (santé et volonté, plus Puissance, Finesse et Résilience pour un PNJ
 * simplifié), avec « Ouvrir la fiche » et « Supprimer ».
 */
import { fill, labels } from "@/shared/i18n";
import { openSheet } from "@/shared/windows/detached";

import type { NpcCard } from "../api";

interface NpcCardItemProps {
  readonly npc: NpcCard;
  readonly onDelete: () => void;
}

export function NpcCardItem({ npc, onDelete }: NpcCardItemProps) {
  const text = labels.npcsTool;
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
      <p className="text-ink-bright truncate text-2xl font-bold">{npc.name}</p>
      <span className="border-gold font-display text-gold self-start rounded-xs border px-2 py-0.5 text-[9px] font-bold tracking-[2px]">
        {text.badge[npc.model]}
      </span>
      <p className="text-ink-muted truncate text-[17px] italic">{npc.concept}</p>
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
