"use client";

/**
 * Image du MJ affichée en grand chez tous.
 *
 * La table est floutée et assombrie, un bandeau annonce la pause et l'image
 * s'affiche en cadre photo avec son nom. Les joueurs ne peuvent rien faire sur
 * la table pendant ce temps ; seul le MJ la referme avec « Reposer l'image ».
 */
import { fill, labels } from "@/shared/i18n";
import { SignedImage } from "@/shared/ui/SignedImage";

import type { LibraryImage } from "../api";

interface ShownImageOverlayProps {
  readonly image: LibraryImage;
  readonly gmName: string;
  readonly isGm: boolean;
  readonly onPutDown: () => void;
}

export function ShownImageOverlay({ image, gmName, isGm, onPutDown }: ShownImageOverlayProps) {
  const text = labels.tableImages;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={image.name}
      className="animate-pause-veil absolute inset-0 z-40 flex flex-col items-center bg-black/70 backdrop-blur-md"
    >
      <p className="border-copper font-display text-ink-bright mt-[74px] flex items-center gap-3 rounded-full border bg-black/60 px-5 py-2 text-[11px] font-bold tracking-[2.5px]">
        <span aria-hidden="true" className="bg-copper size-2 rounded-full" />
        {text.pauseBanner}
      </p>
      <figure className="animate-image-grow mt-6 flex flex-col items-center">
        <SignedImage
          url={image.url}
          alt={image.name}
          className="max-h-[560px] max-w-[940px] border-[7px] border-[#efe6cf] object-contain shadow-[0_24px_60px_rgb(0_0_0/0.85),0_0_40px_rgb(255_90_20/0.18)]"
        />
        <figcaption className="mt-5 flex flex-col items-center gap-1">
          <span className="text-ink-bright text-[26px] font-bold">{image.name}</span>
          <span className="text-ink-muted text-[15px] italic">
            {fill(text.shownBy, { gm: gmName })}
          </span>
          {isGm && (
            <button
              type="button"
              autoFocus
              onClick={onPutDown}
              className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright mt-4 h-10 cursor-pointer rounded-xs border bg-linear-to-b px-6 text-[12px] font-bold tracking-[2.5px] shadow-[0_0_16px_rgb(216_53_44/0.33)] hover:brightness-110"
            >
              {text.putDown}
            </button>
          )}
        </figcaption>
      </figure>
    </div>
  );
}
