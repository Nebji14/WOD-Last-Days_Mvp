"use client";

/**
 * Image de la table regardée en grand, sur cet écran seulement : les autres
 * participants ne voient rien et la partie n'est pas mise en pause.
 *
 * Échap, un clic sur l'image ou à côté, ou « RÉDUIRE » la referment ; les
 * flèches passent d'une image à l'autre.
 */
import { type KeyboardEvent, useEffect, useRef } from "react";

import { labels } from "@/shared/i18n";
import { SignedImage } from "@/shared/ui/SignedImage";

import type { LibraryImage } from "../api";
import { neighbour } from "../pile";

const ARROW =
  "border-line-strong text-ink hover:border-gold hover:text-gold flex size-12 shrink-0 cursor-pointer items-center justify-center rounded-full border bg-black/70 text-2xl transition-colors";

interface TableImageViewerProps {
  readonly pile: readonly LibraryImage[];
  /** Image regardée, `null` quand la vue est fermée. */
  readonly image: LibraryImage | null;
  readonly onView: (imageId: string) => void;
  readonly onClose: () => void;
}

export function TableImageViewer({ pile, image, onView, onClose }: TableImageViewerProps) {
  const text = labels.tableImages;
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog === null) return;
    if (image !== null && !dialog.open) dialog.showModal();
    if (image === null && dialog.open) dialog.close();
  }, [image]);

  function go(step: 1 | -1): void {
    const next = image === null ? null : neighbour(pile, image.id, step);
    if (next !== null) {
      onView(next.id);
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLDialogElement>): void {
    if (event.key === "ArrowLeft") {
      go(-1);
    } else if (event.key === "ArrowRight") {
      go(1);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      aria-label={image?.name ?? text.viewerClose}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => event.target === event.currentTarget && onClose()}
      onKeyDown={onKeyDown}
      className="text-ink m-auto h-dvh max-h-none w-screen max-w-none bg-transparent p-0 backdrop:bg-black/90"
    >
      {image !== null && (
        <figure className="pointer-events-none flex size-full flex-col items-center gap-3 p-4">
          <button
            type="button"
            onClick={onClose}
            aria-label={`${text.viewerClose} ${image.name}`}
            className="pointer-events-auto flex min-h-0 w-full flex-1 cursor-zoom-out items-center justify-center"
          >
            <SignedImage url={image.url} alt={image.name} className="size-full object-contain" />
          </button>
          <figcaption className="pointer-events-auto flex max-w-full shrink-0 items-center gap-4">
            {pile.length > 1 && (
              <button
                type="button"
                onClick={() => go(-1)}
                aria-label={text.viewerPrevious}
                className={ARROW}
              >
                ‹
              </button>
            )}
            <span className="text-ink-bright min-w-0 truncate text-xl font-semibold">
              {image.name}
            </span>
            <button
              type="button"
              autoFocus
              onClick={onClose}
              className="border-gold font-display text-gold hover:bg-gold hover:text-abyss min-h-11 shrink-0 cursor-pointer rounded-xs border bg-black/70 px-5 text-[12px] font-bold tracking-[2px] transition-colors"
            >
              {text.viewerClose}
            </button>
            {pile.length > 1 && (
              <button
                type="button"
                onClick={() => go(1)}
                aria-label={text.viewerNext}
                className={ARROW}
              >
                ›
              </button>
            )}
          </figcaption>
        </figure>
      )}
    </dialog>
  );
}
