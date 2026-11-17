/**
 * [Panneau — Sur la table] de l'outil Images (04b).
 *
 * L'image affichée en grand, avec [Reposer l'image] (Q04b-1), puis la pile, la
 * plus récente en haut ; chaque ligne « Posée — … » a [Retirer de la table]
 * (04b-I6, US-031 · CA6). [Rappel — affichage] en bas.
 */
import type { ReactNode } from "react";

import { fill, labels } from "@/shared/i18n";
import { SignedImage } from "@/shared/ui/SignedImage";

import type { LibraryImage, TableScene } from "../api";

const LINK = "font-display cursor-pointer text-[9px] font-bold tracking-[2px] hover:brightness-125";

interface OnTablePanelProps {
  readonly scene: TableScene;
  readonly onPutDown: () => void;
  readonly onRemove: (imageId: string) => void;
}

function Row({ image, children }: { readonly image: LibraryImage; readonly children: ReactNode }) {
  return (
    <li className="border-line flex items-center gap-4 rounded-xs border p-2.5">
      <SignedImage
        url={image.url}
        alt=""
        className="border-ink/80 h-[38px] w-[64px] shrink-0 border-2 object-cover"
      />
      <div className="min-w-0">
        <p className="text-ink truncate text-[17px]">{image.name}</p>
        {children}
      </div>
    </li>
  );
}

export function OnTablePanel({ scene, onPutDown, onRemove }: OnTablePanelProps) {
  const text = labels.imagesTool;

  return (
    <section
      aria-label={fill(text.onTable, { count: scene.pile.length })}
      className="border-line bg-panel flex min-h-0 flex-col rounded-xs border px-4 py-5"
    >
      <h2 className="font-display text-gold text-[12px] font-bold tracking-[3px]">
        {fill(text.onTable, { count: scene.pile.length })}
      </h2>
      <p className="text-ink-muted mt-2 mb-4 text-[15px] italic">{text.onTableHint}</p>
      <ul className="flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto">
        {scene.shown !== null && (
          <Row image={scene.shown}>
            <p className="font-display text-gold text-[9px] font-bold tracking-[2px]">
              {text.shownNow}
            </p>
            <button type="button" onClick={onPutDown} className={`${LINK} text-copper-light`}>
              {text.putDown}
            </button>
          </Row>
        )}
        {scene.pile.map((image) => (
          <Row key={image.id} image={image}>
            <button
              type="button"
              onClick={() => onRemove(image.id)}
              className={`${LINK} text-danger`}
            >
              {text.removeFromTable}
            </button>
          </Row>
        ))}
        {scene.shown === null && scene.pile.length === 0 && (
          <li className="text-ink-faint text-[15px] italic">{text.onTableEmpty}</li>
        )}
      </ul>
      <p className="text-ink-faint mt-4 text-[15px] italic">{text.onTableReminder}</p>
    </section>
  );
}
