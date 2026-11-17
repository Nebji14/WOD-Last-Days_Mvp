"use client";

/**
 * Bibliothèque d'images : compteurs, création de dossier, chargement d'images,
 * recherche, arborescence, contenu du dossier ouvert et zone de dépôt.
 */
import { useRef, useState } from "react";

import { fill, labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";

import {
  createFolder,
  deleteFolder,
  deleteImage,
  type Library,
  type LibraryImage,
  moveFolder,
  moveImage,
  renameFolder,
  renameImage,
  showImage,
} from "../api";
import { folderPath, imagesIn, isWithin, searchImages } from "../tree";
import type { ImageLibraryState } from "../useImageLibrary";
import type { DraggedItem } from "./dragData";
import { DropZone } from "./DropZone";
import { FolderContent } from "./FolderContent";
import { FolderTree } from "./FolderTree";
import { ImagePreview } from "./ImagePreview";

const ACCEPTED = "image/png,image/jpeg,image/webp,image/gif";

type Pending =
  | { readonly kind: "image"; readonly image: LibraryImage }
  | { readonly kind: "folder"; readonly id: string; readonly name: string };

interface LibraryPanelProps extends Omit<ImageLibraryState, "library" | "scene" | "errorCode"> {
  readonly library: Library;
  readonly onLocalError: (code: string) => void;
}

export function LibraryPanel({
  library,
  act,
  upload,
  uploads,
  dismissUpload,
  onLocalError,
}: LibraryPanelProps) {
  const text = labels.imagesTool;
  const { folders, images } = library;
  const fileInput = useRef<HTMLInputElement>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set());
  const [query, setQuery] = useState("");
  const [renamingFolder, setRenamingFolder] = useState<string | null>(null);
  const [renamingImage, setRenamingImage] = useState<string | null>(null);
  const [preview, setPreview] = useState<LibraryImage | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);

  const openFolder = folders.find((folder) => folder.id === openId) ?? null;
  const searching = query.trim() !== "";
  const shown = searching
    ? searchImages(images, folders, query)
    : imagesIn(images, openFolder?.id ?? null);

  /** Ouvre un dossier et déplie ses parents, pour qu'il soit visible dans l'arborescence. */
  const reveal = (folderId: string | null) => {
    setOpenId(folderId);
    const parents = folderPath(folders, folderId)
      .slice(0, -1)
      .map((f) => f.id);
    setExpanded((current) => new Set([...current, ...parents]));
  };

  /** Crée « Nouveau dossier », l'ouvre et met son nom en saisie. */
  const newFolder = async (parentId: string | null) => {
    const created: { id: string | null } = { id: null };
    const done = await act(async () => {
      created.id = await createFolder(text.defaultFolderName, parentId);
    });
    if (done && created.id !== null) {
      setExpanded((current) => new Set([...current, ...(parentId === null ? [] : [parentId])]));
      setOpenId(created.id);
      setRenamingFolder(created.id);
    }
  };

  const renameOpenFolder = () => {
    if (openFolder !== null) {
      reveal(openFolder.id);
      setRenamingFolder(openFolder.id);
    }
  };

  const askFolderDeletion = () => {
    if (openFolder !== null) {
      setPending({ kind: "folder", id: openFolder.id, name: openFolder.name });
    }
  };

  const onDrop = (item: DraggedItem, target: string | null) => {
    if (item.kind === "image") {
      void act(() => moveImage(item.id, target));
    } else if (item.id !== target && isWithin(folders, item.id, target)) {
      onLocalError("folder_cycle");
    } else if (item.id !== target) {
      void act(() => moveFolder(item.id, target));
    }
  };

  const confirmDeletion = () => {
    if (pending?.kind === "image") {
      void act(() => deleteImage(pending.image.id));
    } else if (pending?.kind === "folder") {
      const parent = folders.find((f) => f.id === pending.id)?.parentId ?? null;
      void act(() => deleteFolder(pending.id)).then((done) => {
        if (done) {
          setOpenId(parent);
        }
      });
    }
    setPending(null);
  };

  return (
    <section
      aria-label={text.library}
      className="border-line bg-panel flex min-h-0 flex-col gap-4 rounded-xs border p-4"
    >
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-display text-gold flex items-baseline gap-3 text-[13px] font-bold tracking-[3px]">
          {text.library}
          <span className="text-ink-muted font-body text-sm font-normal tracking-normal italic">
            {fill(text.counts, { images: images.length, folders: folders.length })}
          </span>
        </h2>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => void newFolder(null)}
            className="border-copper font-display text-copper-light h-[38px] cursor-pointer rounded-xs border px-3 text-[11px] font-bold tracking-[2px] hover:brightness-125"
          >
            {text.newFolder}
          </button>
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright h-[38px] cursor-pointer rounded-xs border bg-linear-to-b px-4 text-[11px] font-bold tracking-[2px] shadow-[0_0_16px_rgb(216_53_44/0.33)] hover:brightness-110"
          >
            {text.upload}
          </button>
          <input
            ref={fileInput}
            type="file"
            multiple
            accept={ACCEPTED}
            className="hidden"
            onChange={(event) => {
              upload(Array.from(event.target.files ?? []), openFolder?.id ?? null);
              event.target.value = "";
            }}
          />
        </div>
      </div>

      <label className="border-line-strong flex h-10 shrink-0 items-center gap-3 rounded-xs border px-3">
        <span aria-hidden="true" className="text-ink-muted">
          ⌕
        </span>
        <span className="sr-only">{text.searchLabel}</span>
        <input
          type="search"
          value={query}
          placeholder={text.searchPlaceholder}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => event.key === "Escape" && setQuery("")}
          className="text-ink placeholder:text-ink-faint min-w-0 flex-1 bg-transparent text-[17px] outline-none placeholder:italic"
        />
        <span className="font-display text-ink-muted text-[9px] font-bold tracking-[2px]">
          {text.searchScope}
        </span>
      </label>

      <div className="grid min-h-0 flex-1 grid-cols-[180px_minmax(0,1fr)] gap-4">
        <FolderTree
          folders={folders}
          images={images}
          openId={openId}
          expanded={expanded}
          renamingId={renamingFolder}
          onOpen={(id) => {
            setQuery("");
            setOpenId(id);
          }}
          onToggle={(id) =>
            setExpanded((current) => {
              const next = new Set(current);
              if (!next.delete(id)) next.add(id);
              return next;
            })
          }
          onRename={(id, name) => {
            setRenamingFolder(null);
            void act(() => renameFolder(id, name));
          }}
          onRenameEnd={() => setRenamingFolder(null)}
          onDrop={onDrop}
        />
        <div className="flex min-h-0 flex-col gap-4">
          <FolderContent
            folders={folders}
            openFolder={openFolder}
            images={shown}
            searching={searching}
            renamingImageId={renamingImage}
            onOpen={reveal}
            onSubFolder={() => void newFolder(openFolder?.id ?? null)}
            onRenameFolder={renameOpenFolder}
            onDeleteFolder={askFolderDeletion}
            onPreview={setPreview}
            onShow={(image) => void act(() => showImage(image.id))}
            onRenameStart={(image) => setRenamingImage(image.id)}
            onRename={(image, name) => {
              setRenamingImage(null);
              void act(() => renameImage(image.id, name));
            }}
            onRenameEnd={() => setRenamingImage(null)}
            onDelete={(image) => setPending({ kind: "image", image })}
          />
          <DropZone
            uploads={uploads}
            onFiles={(files) => upload(files, openFolder?.id ?? null)}
            onDismiss={dismissUpload}
          />
        </div>
      </div>

      <ImagePreview image={preview} onClose={() => setPreview(null)} />
      <ConfirmDialog
        open={pending !== null}
        title={pending?.kind === "folder" ? text.deleteFolderTitle : text.deleteImageTitle}
        question={
          pending?.kind === "folder"
            ? fill(text.deleteFolderQuestion, { name: pending.name })
            : fill(text.deleteImageQuestion, { name: pending?.image.name ?? "" })
        }
        confirmLabel={text.delete}
        cancelLabel={text.cancel}
        onConfirm={confirmDeletion}
        onCancel={() => setPending(null)}
      />
    </section>
  );
}
