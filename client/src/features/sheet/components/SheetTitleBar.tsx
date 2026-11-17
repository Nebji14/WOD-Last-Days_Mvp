"use client";

/**
 * [Barre de titre] de la fiche (05).
 *
 * Nom du personnage et joueur propriétaire, [Bouton — Lancer les dés] (placé
 * mais inactif, US-014 après le MVP, 05-L3), [Bascule — Recto / Verso] à trois
 * faces, [Bouton — Modifier] ou [Badge — Mode modification] + [Bouton —
 * Terminer] (05-I2), [Bouton — Fermer] (05-I8 : tout est déjà enregistré).
 */
import { fill, labels } from "@/shared/i18n";

export type SheetFace = "recto" | "verso" | "notes";
const FACES: readonly SheetFace[] = ["recto", "verso", "notes"];

const OUTLINE_BUTTON =
  "border-line-strong font-display text-ink flex h-[34px] cursor-pointer items-center gap-2.5 rounded-xs border px-3.5 text-[11px] font-bold tracking-[2.5px] hover:brightness-125";

interface SheetTitleBarProps {
  readonly name: string;
  readonly owner: string;
  readonly face: SheetFace;
  readonly onFace: (face: SheetFace) => void;
  readonly editing: boolean;
  readonly onEditing: (editing: boolean) => void;
}

export function SheetTitleBar(props: SheetTitleBarProps) {
  const { name, owner, face, onFace, editing, onEditing } = props;
  const text = labels.sheet;

  return (
    <header className="border-line bg-panel flex h-[60px] shrink-0 items-center gap-6 border-b px-8">
      <div className="max-w-[320px] min-w-0 shrink">
        <p className="font-display text-gold text-[10px] font-bold tracking-[3px]">
          {text.windowTitle}
        </p>
        <h1 className="text-ink-bright truncate text-base font-semibold">
          {fill(text.titleLine, { name: name || "—", owner })}
        </h1>
      </div>

      <button
        type="button"
        disabled
        title={text.rollDiceSoon}
        className="border-gold font-display text-ink flex h-[34px] cursor-not-allowed items-center gap-2.5 rounded-xs border px-3.5 text-[11px] font-bold tracking-[2.5px] opacity-60"
      >
        <span aria-hidden="true" className="text-gold text-base">
          ⚄
        </span>
        {text.rollDice}
      </button>

      <div
        role="tablist"
        aria-label={text.facesLabel}
        className="border-line-strong flex h-8 overflow-hidden rounded-xs border"
      >
        {FACES.map((candidate) => (
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
