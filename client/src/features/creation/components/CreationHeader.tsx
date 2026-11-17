"use client";

/**
 * Barre de titre de la création : titre, joueur et étape, [Bouton — Fermer].
 * Une création entamée n'est abandonnée qu'après confirmation (Q06-1).
 */
import { useState } from "react";

import { labels } from "@/shared/i18n";

const SMALL_ACTION = "font-display cursor-pointer text-[10px] font-bold tracking-[2px]";

interface CreationHeaderProps {
  readonly subtitle: string;
  readonly dirty: boolean;
}

export function CreationHeader({ subtitle, dirty }: CreationHeaderProps) {
  const text = labels.creation;
  const [asking, setAsking] = useState(false);

  return (
    <header className="border-line bg-panel flex h-[60px] shrink-0 items-center justify-between border-b px-8">
      <div>
        <h1 className="font-display text-ink-bright text-[20px] font-bold tracking-[4px]">
          {text.windowTitle}
        </h1>
        <p className="text-ink-muted text-sm italic">{subtitle}</p>
      </div>
      {asking ? (
        <div role="alertdialog" aria-label={text.abandon} className="flex items-center gap-4">
          <span className="text-ink text-[15px] italic">{text.abandon}</span>
          <button
            type="button"
            autoFocus
            onClick={() => window.close()}
            className={`${SMALL_ACTION} text-danger`}
          >
            {text.abandonConfirm}
          </button>
          <button
            type="button"
            onClick={() => setAsking(false)}
            className={`${SMALL_ACTION} text-ink-muted`}
          >
            {text.abandonCancel}
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => (dirty ? setAsking(true) : window.close())}
          className="border-line-strong font-display text-ink flex h-[34px] cursor-pointer items-center gap-2.5 rounded-xs border px-3.5 text-[11px] font-bold tracking-[2.5px] hover:brightness-125"
        >
          {text.close}
          <span aria-hidden="true">✕</span>
        </button>
      )}
    </header>
  );
}
