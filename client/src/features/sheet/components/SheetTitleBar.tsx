"use client";

/**
 * Barre de titre de la fiche.
 *
 * Nom du personnage et de son joueur (pour un PNJ : catégorie et modèle),
 * bouton du mode jet de dés, choix de la face, bouton
 * Modifier / Terminer et bouton Fermer (tout est déjà enregistré).
 */
import type { NpcModel } from "@/features/characters/model";
import { fill, labels } from "@/shared/i18n";

export type SheetFace = "recto" | "verso" | "notes";
const FACES: readonly SheetFace[] = ["recto", "verso", "notes"];
const NPC_FACES: readonly SheetFace[] = ["recto", "verso"];

const OUTLINE_BUTTON =
  "border-line-strong font-display text-ink flex h-[34px] cursor-pointer items-center gap-2.5 rounded-xs border px-3.5 text-[11px] font-bold tracking-[2.5px] hover:brightness-125";

interface SheetTitleBarProps {
  readonly name: string;
  readonly owner: string;
  /** Modèle et chemin de catégorie d'un PNJ ; `null` pour un personnage joueur. */
  readonly npc: { readonly model: NpcModel; readonly category: string } | null;
  readonly face: SheetFace;
  readonly onFace: (face: SheetFace) => void;
  readonly editing: boolean;
  readonly onEditing: (editing: boolean) => void;
  /** Mode jet : les traits de la fiche se cliquent pour composer la réserve. */
  readonly rolling: boolean;
  readonly onRolling: (rolling: boolean) => void;
}

export function SheetTitleBar(props: SheetTitleBarProps) {
  const { name, owner, npc, face, onFace, editing, onEditing, rolling, onRolling } = props;
  const text = labels.sheet;

  return (
    <header className="border-line bg-panel flex h-[60px] shrink-0 items-center gap-6 border-b px-8">
      <div className="max-w-[320px] min-w-0 shrink">
        <p className="font-display text-gold text-[10px] font-bold tracking-[3px]">
          {npc === null ? text.windowTitle : labels.npcSheet.windowTitle}
        </p>
        <h1 className="text-ink-bright truncate text-base font-semibold">
          {npc === null
            ? fill(text.titleLine, { name: name || "—", owner })
            : [name || "—", npc.category].filter(Boolean).join(" · ")}
        </h1>
      </div>

      <button
        type="button"
        aria-pressed={rolling}
        onClick={() => onRolling(!rolling)}
        className={`border-gold font-display flex h-[34px] cursor-pointer items-center gap-2.5 rounded-xs border px-3.5 text-[11px] font-bold tracking-[2.5px] hover:brightness-125 ${
          rolling ? "bg-gold text-abyss" : "text-ink"
        }`}
      >
        <span aria-hidden="true" className={rolling ? "text-base" : "text-gold text-base"}>
          ⚄
        </span>
        {rolling ? labels.dice.closeRollMode : text.rollDice}
      </button>

      <div
        role="tablist"
        aria-label={text.facesLabel}
        className="border-line-strong flex h-8 overflow-hidden rounded-xs border"
      >
        {(npc === null ? FACES : NPC_FACES).map((candidate) => (
          <button
            key={candidate}
            type="button"
            role="tab"
            aria-selected={candidate === face}
            onClick={() => onFace(candidate)}
            className={`font-display w-[83px] cursor-pointer text-[11px] font-bold tracking-[2.5px] ${
              candidate === face ? "bg-gold text-abyss" : "text-ink-muted hover:text-ink"
            }`}
          >
            {text.faces[candidate]}
          </button>
        ))}
      </div>

      {npc !== null && (
        <span className="border-gold font-display text-gold rounded-xs border px-2 py-0.5 text-[9px] font-bold tracking-[2px]">
          {labels.npcsTool.badge[npc.model]}
        </span>
      )}
      {editing && (
        <span className="border-copper bg-copper-deep/30 font-display text-copper-light rounded-xs border px-2 py-0.5 text-[9px] font-bold tracking-[1.5px]">
          {text.editing}
        </span>
      )}

      <div className="ml-auto flex items-center gap-3.5">
        <button
          type="button"
          onClick={() => onEditing(!editing)}
          className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright h-[34px] w-[120px] cursor-pointer rounded-xs border bg-linear-to-b text-[11px] font-bold tracking-[2.5px] shadow-[0_0_12px_rgb(216_53_44/0.3)] hover:brightness-110"
        >
          {editing ? text.done : text.edit}
        </button>
        <button type="button" onClick={() => window.close()} className={OUTLINE_BUTTON}>
          {text.close}
          <span aria-hidden="true">✕</span>
        </button>
      </div>
    </header>
  );
}
