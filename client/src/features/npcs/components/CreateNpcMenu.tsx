"use client";

/**
 * [Bouton — Créer un PNJ] et [Menu — Choix du modèle] (04c-I3, RM-021).
 * Le choix crée une feuille vierge, rangée dans la catégorie sélectionnée.
 */
import { useState } from "react";

import type { NpcModel } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

const MODELS: readonly NpcModel[] = ["full", "simplified"];

export function CreateNpcMenu({ onCreate }: { readonly onCreate: (model: NpcModel) => void }) {
  const text = labels.npcsTool;
  const [open, setOpen] = useState(false);

  return (
    <div className="relative" onKeyDown={(event) => event.key === "Escape" && setOpen(false)}>
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright h-[38px] cursor-pointer rounded-xs border bg-linear-to-b px-12 text-[12px] font-bold tracking-[2px] shadow-[0_0_16px_rgb(216_53_44/0.33)] hover:brightness-110"
      >
        {text.create}
      </button>
      {open && (
        <ul
          role="menu"
          aria-label={text.chooseModel}
          className="border-gold bg-panel absolute top-[46px] right-0 z-20 w-[250px] rounded-xs border p-1.5 shadow-[0_12px_30px_rgb(0_0_0/0.7)]"
        >
          {MODELS.map((model, index) => (
            <li key={model} role="none">
              <button
                type="button"
                role="menuitem"
                autoFocus={index === 0}
                onClick={() => {
                  setOpen(false);
                  onCreate(model);
                }}
                className="w-full cursor-pointer rounded-xs px-3 py-2.5 text-left hover:bg-[#2a2119] focus:bg-[#2a2119] focus:outline-none"
              >
                <span className="text-ink-bright block text-lg font-semibold">
                  {text.models[model].title}
                </span>
                <span className="text-ink-muted block text-sm italic">
                  {text.models[model].hint}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
