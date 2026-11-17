"use client";

/**
 * Aperçu en grand d'une image, dans la fenêtre de l'outil seulement (04b-I2) :
 * rien n'est montré à la table. Échap, le fond ou le bouton referment.
 */
import { useEffect, useRef } from "react";

import { labels } from "@/shared/i18n";
import { SignedImage } from "@/shared/ui/SignedImage";

import type { LibraryImage } from "../api";

interface ImagePreviewProps {
  readonly image: LibraryImage | null;
  readonly onClose: () => void;
}

export function ImagePreview({ image, onClose }: ImagePreviewProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (dialog === null) return;
    if (image !== null && !dialog.open) dialog.showModal();
    if (image === null && dialog.open) dialog.close();
  }, [image]);

  return (
    <dialog
      ref={ref}
      aria-label={image?.name ?? labels.imagesTool.previewClose}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => event.target === event.currentTarget && onClose()}
      className="m-auto max-h-[90vh] max-w-[90vw] bg-transparent p-0 backdrop:bg-black/80"
    >
      {image !== null && (
        <figure className="flex flex-col items-center gap-3">
          <SignedImage
            url={image.url}
            alt={image.name}
            className="border-ink max-h-[78vh] max-w-[86vw] border-[6px] object-contain"
          />
          <figcaption className="text-ink-bright flex items-center gap-4 text-xl font-semibold">
            {image.name}
            <button
              type="button"
              autoFocus
              onClick={onClose}
              className="border-line-strong font-display text-ink cursor-pointer rounded-xs border px-3 py-1 text-[11px] font-bold tracking-[2px]"
            >
              {labels.imagesTool.close} ✕
            </button>
          </figcaption>
        </figure>
      )}
    </dialog>
  );
}
