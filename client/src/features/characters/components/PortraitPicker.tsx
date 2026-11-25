"use client";

/**
 * Médaillon modifiable d'une forme : un clic sur la photo ou sur son bouton
 * ouvre la fenêtre qui permet de la choisir, la repositionner ou la retirer.
 */
import { useState } from "react";

import { labels } from "@/shared/i18n";

import type { PortraitFiles } from "../portrait";
import { Portrait } from "./Portrait";
import { PortraitDialog } from "./PortraitDialog";

interface PortraitPickerProps {
  /** Nom du fichier de l'image actuelle, `null` sans image. */
  readonly portrait: string | null;
  /** Nom du personnage ou de la forme. */
  readonly name: string;
  /** Taille et taille de texte du médaillon. */
  readonly className: string;
  readonly busy: boolean;
  /** Libellé court, là où la place manque. */
  readonly compact?: boolean;
  readonly onSave: (files: PortraitFiles) => void;
  readonly onRemove: () => void;
}

/** Pictogramme d'appareil photo. */
function CameraIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="size-4 shrink-0"
    >
      <path d="M4 8h3l2-3h6l2 3h3v11H4z" />
      <circle cx="12" cy="13" r="3.5" />
    </svg>
  );
}

export function PortraitPicker(props: PortraitPickerProps) {
  const { portrait, name, className, busy, compact = false, onSave, onRemove } = props;
  const text = labels.sheet.portrait;
  const [open, setOpen] = useState(false);
  const action = portrait === null ? text.add : text.edit;

  return (
    <div className="flex shrink-0 flex-col items-center gap-2.5">
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={busy}
        aria-label={`${action} : ${name}`}
        title={action}
        className="group relative cursor-pointer rounded-full disabled:cursor-wait"
      >
        <Portrait
          portrait={portrait}
          name={name}
          className={`${className} ${busy ? "animate-pulse" : ""}`}
        />
        <span className="text-ink-bright absolute inset-0 flex items-center justify-center rounded-full bg-black/60 opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
          <CameraIcon />
        </span>
      </button>
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={busy}
        aria-label={`${action} : ${name}`}
        className="border-gold bg-gold/10 font-display text-gold hover:bg-gold hover:text-abyss flex min-h-10 cursor-pointer items-center gap-2 rounded-xs border px-3.5 text-[12px] font-bold tracking-[1.5px] whitespace-nowrap transition-colors disabled:cursor-wait disabled:opacity-60"
      >
        <CameraIcon />
        {busy ? text.sending : compact ? text.short : action}
      </button>
      {open && (
        <PortraitDialog
          portrait={portrait}
          name={name}
          onSave={(files) => {
            setOpen(false);
            onSave(files);
          }}
          onRemove={() => {
            setOpen(false);
            onRemove();
          }}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}
