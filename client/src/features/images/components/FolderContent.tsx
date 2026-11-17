"use client";

/**
 * Contenu du dossier ouvert (04b) : [Fil d'Ariane — dossier ouvert],
 * [Actions — dossier ouvert (CRUD)] et [Grille d'images], 3 colonnes.
 * En recherche, la grille montre les résultats de tous les dossiers, chacun
 * avec son chemin (04b-I8).
 */
import { labels } from "@/shared/i18n";

import type { ImageFolder, LibraryImage } from "../api";
import { folderPath } from "../tree";
import { ImageCard } from "./ImageCard";

const ACTION = "font-display text-copper cursor-pointer text-[10px] font-bold tracking-[2px] hover:brightness-125";

interface FolderContentProps {
  readonly folders: readonly ImageFolder[];
  readonly openFolder: ImageFolder | null;
  readonly images: readonly LibraryImage[];
  /** Résultats de recherche : chaque carte affiche son chemin de dossier. */
  readonly searching: boolean;
  readonly renamingImageId: string | null;
  readonly onOpen: (folderId: string | null) => void;
  readonly onSubFolder: () => void;
  readonly onRenameFolder: () => void;
  readonly onDeleteFolder: () => void;
  readonly onPreview: (image: LibraryImage) => void;
  readonly onShow: (image: LibraryImage) => void;
  readonly onRenameStart: (image: LibraryImage) => void;
  readonly onRename: (image: LibraryImage, name: string) => void;
  readonly onRenameEnd: () => void;
  readonly onDelete: (image: LibraryImage) => void;
}

export function FolderContent(props: FolderContentProps) {
  const { folders, openFolder, images, searching } = props;
  const text = labels.imagesTool;
  const crumbs = folderPath(folders, openFolder?.id ?? null);
  const pathOf = (image: LibraryImage) =>
    [text.allImages, ...folderPath(folders, image.folderId).map((f) => f.name)].join(" › ");

  return (
    <div className="flex min-h-0 flex-col gap-3">
      {!searching && (
        <div className="flex items-center justify-between gap-4">
          <nav aria-label={text.folders} className="text-ink flex min-w-0 items-center gap-2 text-[17px]">
            <button type="button" onClick={() => props.onOpen(null)} className="cursor-pointer hover:underline">
              {text.allImages}
            </button>
            {crumbs.map((folder) => (
              <span key={folder.id} className="flex min-w-0 items-center gap-2">
                <span aria-hidden="true">›</span>
                <button
                  type="button"
                  onClick={() => props.onOpen(folder.id)}
                  className="cursor-pointer truncate hover:underline"
                >
                  {folder.name}
                </button>
              </span>
            ))}
          </nav>
          {openFolder !== null && (
            <div className="flex shrink-0 items-center gap-3">
              <button type="button" onClick={props.onSubFolder} className={ACTION}>
                {text.subFolder}
              </button>
              <span aria-hidden="true" className="text-ink-faint">·</span>
              <button type="button" onClick={props.onRenameFolder} className={ACTION}>
                {text.rename}
              </button>
              <span aria-hidden="true" className="text-ink-faint">·</span>
              <button type="button" onClick={props.onDeleteFolder} className={`${ACTION} text-danger`}>
                {text.delete}
              </button>
            </div>
          )}
        </div>
      )}
      {images.length === 0 ? (
        <p className="text-ink-faint py-6 text-lg italic">
          {searching ? text.noResult : text.emptyFolder}
        </p>
      ) : (
        <ul className="grid min-h-0 grid-cols-3 gap-x-5 gap-y-4 overflow-y-auto pr-1">
          {images.map((image) => (
            <ImageCard
              key={image.id}
              image={image}
              path={searching ? pathOf(image) : undefined}
              renaming={props.renamingImageId === image.id}
              onPreview={() => props.onPreview(image)}
              onShow={() => props.onShow(image)}
              onRenameStart={() => props.onRenameStart(image)}
              onRename={(name) => props.onRename(image, name)}
              onRenameEnd={props.onRenameEnd}
              onDelete={() => props.onDelete(image)}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
