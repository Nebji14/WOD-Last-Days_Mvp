"use client";

/**
 * Pile des images posées sur la table.
 *
 * Tout à gauche du tapis, pour ne pas gêner les dés : miniatures à bord blanc
 * posées en éventail, la dernière au-dessus, avec un compteur. Un clic ouvre la
 * galerie de toutes les images posées ; le MJ peut y retirer une image. Chacun
 * peut y regarder une image en grand, sur son écran seulement.
 */
import { useEffect, useRef, useState } from "react";

import { fill, labels } from "@/shared/i18n";
import { SignedImage } from "@/shared/ui/SignedImage";

import type { LibraryImage } from "../api";
import { TableImageViewer } from "./TableImageViewer";

/** Rotation des trois miniatures visibles, de la plus ancienne à la plus récente. */
const FAN = ["-rotate-[10deg]", "rotate-[7deg]", "-rotate-2"] as const;

interface TableImagePileProps {
  readonly pile: readonly LibraryImage[];
  readonly isGm: boolean;
  /** Le MJ montre une image à tous : elle passe devant la galerie. */
  readonly paused: boolean;
  readonly onRemove: (imageId: string) => void;
}

export function TableImagePile({ pile, isGm, paused, onRemove }: TableImagePileProps) {
  const text = labels.tableImages;
  const [open, setOpen] = useState(false);
  const [viewedId, setViewedId] = useState<string | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const visible = pile.slice(0, 3).reverse();
  const galleryOpen = open && !paused;
  const viewed = galleryOpen ? (pile.find((image) => image.id === viewedId) ?? null) : null;

  useEffect(() => {
    const element = dialog.current;
    if (element === null) return;
    if (galleryOpen && !element.open) element.showModal();
    if (!galleryOpen && element.open) element.close();
  }, [galleryOpen]);

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
        <ul className="grid max-h-[70vh] grid-cols-1 gap-5 overflow-y-auto p-6 sm:grid-cols-2">
          {pile.map((image) => (
            <li key={image.id} className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => setViewedId(image.id)}
                aria-label={fill(text.viewLabel, { name: image.name })}
                className="group relative cursor-zoom-in"
              >
                <SignedImage
                  url={image.url}
                  alt={image.name}
                  className="aspect-[4/3] w-full border-4 border-[#efe6cf] object-contain"
                />
                <span
                  aria-hidden="true"
                  className="border-gold font-display text-gold absolute right-3 bottom-3 rounded-xs border bg-black/80 px-3 py-1.5 text-[11px] font-bold tracking-[2px] group-hover:bg-gold group-hover:text-abyss"
                >
                  {text.view}
                </span>
              </button>
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
      <TableImageViewer
        pile={pile}
        image={viewed}
        onView={setViewedId}
        onClose={() => setViewedId(null)}
      />
    </>
  );
}
