"use client";

/**
 * Carte « Image — … » de la grille (04b) : vignette, nom, [Badge — Sur la table].
 *
 * Au survol ou au clavier : voile + [Afficher à la table], [Renommer],
 * [Supprimer de la bibliothèque] (04b-I2). Un clic sur la vignette ouvre
 * l'aperçu sans rien montrer à la table. La carte se glisse sur un dossier
 * pour l'y ranger (04b-I10).
 */
import { labels } from "@/shared/i18n";
import { SignedImage } from "@/shared/ui/SignedImage";

import type { LibraryImage } from "../api";
import { startDrag } from "./dragData";
import { InlineName } from "./InlineName";

const IMAGE_NAME_MAX = 120;
const OVERLAY_BUTTON =
  "font-display h-6 w-[156px] cursor-pointer rounded-xs border text-[10px] font-bold tracking-[2px]";

interface ImageCardProps {
  readonly image: LibraryImage;
  /** Chemin du dossier, affiché sous le nom dans les résultats de recherche (04b-I8). */
  readonly path?: string;
  readonly renaming: boolean;
  readonly onPreview: () => void;
  readonly onShow: () => void;
  readonly onRenameStart: () => void;
  readonly onRename: (name: string) => void;
  readonly onRenameEnd: () => void;
  readonly onDelete: () => void;
}

export function ImageCard(props: ImageCardProps) {
  const { image } = props;
  const text = labels.imagesTool;

  return (
    <li
      draggable={!props.renaming}
      onDragStart={(event) => startDrag(event, { kind: "image", id: image.id })}
      className="flex flex-col gap-2"
    >
      <div className="group border-line bg-field relative aspect-[184/118] overflow-hidden rounded-xs border">
        <SignedImage url={image.url} alt="" className="size-full object-cover" />
        <button
          type="button"
          aria-label={image.name}
          onClick={props.onPreview}
          className="absolute inset-0 cursor-zoom-in"
        />
        {image.onTable && (
          <span className="bg-gold font-display pointer-events-none absolute top-2 left-2 rounded-xs px-2 py-0.5 text-[9px] font-bold tracking-[2px] text-[#120c0a]">
            {text.onTableBadge}
          </span>
        )}
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-1.5 bg-black/70 opacity-0 transition-opacity group-focus-within:pointer-events-auto group-focus-within:opacity-100 group-hover:pointer-events-auto group-hover:opacity-100">
          <button
            type="button"
            onClick={props.onShow}
            className={`${OVERLAY_BUTTON} from-blood-from to-blood-to border-blood-line text-ink-bright bg-linear-to-b`}
          >
            {text.showAtTable}
          </button>
          <button
            type="button"
            onClick={props.onRenameStart}
            className={`${OVERLAY_BUTTON} border-ink-muted bg-panel text-ink`}
          >
            {text.rename}
          </button>
          <button
            type="button"
            onClick={props.onDelete}
            className={`${OVERLAY_BUTTON} border-line-strong bg-panel text-danger`}
          >
            {text.delete}
          </button>
        </div>
      </div>
      {props.renaming ? (
        <InlineName
          initial={image.name}
          label={text.imageNameLabel}
          maxLength={IMAGE_NAME_MAX}
          onSubmit={props.onRename}
          onCancel={props.onRenameEnd}
          className="h-7 text-[16px]"
        />
      ) : (
        <p className="text-ink truncate text-[17px]">{image.name}</p>
      )}
      {props.path !== undefined && (
        <p className="text-ink-faint -mt-1.5 truncate text-sm italic">{props.path}</p>
      )}
    </li>
  );
}
