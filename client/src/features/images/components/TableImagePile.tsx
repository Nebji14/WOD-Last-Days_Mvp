"use client";

/**
 * [Pile d'images du MJ (sur la table)] (03, décision du 2026-11-16).
 *
 * Tout à gauche du tapis, pour ne jamais gêner les dés : miniatures à bord
 * blanc, posées en éventail (−10°, +7°, −2°), la dernière posée au-dessus, et
 * [Compteur d'images]. Un clic ouvre la galerie de toutes les images posées
 * (03-I5) : consultation pour les joueurs, retrait de la table pour le MJ
 * (03-MJ-I3).
 */
import { useEffect, useRef, useState } from "react";

import { fill, labels } from "@/shared/i18n";
import { SignedImage } from "@/shared/ui/SignedImage";

import type { LibraryImage } from "../api";

/** Rotation des trois miniatures visibles, de la plus ancienne à la plus récente. */
const FAN = ["-rotate-[10deg]", "rotate-[7deg]", "-rotate-2"] as const;

interface TableImagePileProps {
  readonly pile: readonly LibraryImage[];
  readonly isGm: boolean;
  readonly onRemove: (imageId: string) => void;
}

export function TableImagePile({ pile, isGm, onRemove }: TableImagePileProps) {
  const text = labels.tableImages;
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const visible = pile.slice(0, 3).reverse();

  useEffect(() => {
    const element = dialog.current;
    if (element === null) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);

  if (pile.length === 0) {
    return null;
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={fill(text.pileLabel, { count: pile.length })}
        className="absolute top-[392px] left-[318px] z-10 size-[96px] cursor-pointer"
      >
        {visible.map((image, index) => (
          <SignedImage
            key={image.id}
            url={image.url}
            alt=""
            className={`absolute inset-x-1 top-3 h-[58px] w-[84px] border-[3px] border-[#efe6cf] object-cover shadow-[0_6px_14px_rgb(0_0_0/0.7)] ${
              FAN[index + FAN.length - visible.length]
            }`}
          />
        ))}
        <span className="bg-copper font-display text-ink-bright absolute -top-1 -right-1 flex size-6 items-center justify-center rounded-full text-[11px] font-bold">
          {pile.length}
        </span>
      </button>

      <dialog
        ref={dialog}
        aria-label={text.galleryTitle}
        onCancel={(event) => {
          event.preventDefault();
          setOpen(false);
        }}
        onClick={(event) => event.target === event.currentTarget && setOpen(false)}
        className="bg-panel border-line-strong text-ink m-auto w-[860px] max-w-[92vw] rounded-xs border p-0 backdrop:bg-black/75"
      >
        <div className="flex items-center justify-between border-line-soft border-b px-6 py-4">
          <h2 className="font-display text-gold text-[13px] font-bold tracking-[3px]">
            {text.galleryTitle}
          </h2>
          <button
            type="button"
            autoFocus
            onClick={() => setOpen(false)}
            className="border-line-strong font-display text-ink cursor-pointer rounded-xs border px-3 py-1.5 text-[11px] font-bold tracking-[2px]"
          >
            {text.galleryClose} ✕
          </button>
        </div>
        <ul className="grid max-h-[70vh] grid-cols-2 gap-5 overflow-y-auto p-6">
          {pile.map((image) => (
            <li key={image.id} className="flex flex-col gap-2">
              <SignedImage
                url={image.url}
                alt={image.name}
                className="aspect-[4/3] w-full border-4 border-[#efe6cf] object-contain"
              />
              <div className="flex items-center justify-between gap-3">
                <span className="text-ink-bright truncate text-lg font-semibold">{image.name}</span>
                {isGm && (
                  <button
                    type="button"
                    onClick={() => onRemove(image.id)}
                    className="font-display text-danger shrink-0 cursor-pointer text-[10px] font-bold tracking-[2px] hover:brightness-125"
                  >
                    {text.removeFromTable}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </dialog>
    </>
  );
}
