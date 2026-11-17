"use client";

/**
 * Arborescence des dossiers d'images.
 *
 * « Toutes les images » puis les dossiers, repliables, avec le nombre d'images.
 * Le dossier ouvert est mis en évidence. On peut déposer sur une ligne une
 * vignette ou un autre dossier pour l'y ranger.
 */
import { type DragEvent, useState } from "react";

import { labels } from "@/shared/i18n";
import { InlineName } from "@/shared/ui/InlineName";

import type { ImageFolder, LibraryImage } from "../api";
import { childrenOf, imageCounts } from "../tree";
import { carriesItem, type DraggedItem, droppedItem, startDrag } from "./dragData";

const FOLDER_NAME_MAX = 60;
const INDENT = ["pl-2", "pl-6", "pl-10", "pl-14", "pl-[4.5rem]"] as const;

interface FolderTreeProps {
  readonly folders: readonly ImageFolder[];
  readonly images: readonly LibraryImage[];
  readonly openId: string | null;
  readonly expanded: ReadonlySet<string>;
  readonly renamingId: string | null;
  readonly onOpen: (folderId: string | null) => void;
  readonly onToggle: (folderId: string) => void;
  readonly onRename: (folderId: string, name: string) => void;
  readonly onRenameEnd: () => void;
  readonly onDrop: (item: DraggedItem, folderId: string | null) => void;
}

export function FolderTree(props: FolderTreeProps) {
  const { folders, images, openId, onOpen, onDrop } = props;
  const text = labels.imagesTool;
  const counts = imageCounts(images);
  const [dropTarget, setDropTarget] = useState<string | null | undefined>(undefined);

  /** Propriétés de dépôt d'une ligne ; `null` désigne « Toutes les images » (racine). */
  const dropProps = (folderId: string | null) => ({
    onDragOver: (event: DragEvent) => {
      if (carriesItem(event)) {
        event.preventDefault();
        setDropTarget(folderId);
      }
    },
    onDragLeave: () => setDropTarget(undefined),
    onDrop: (event: DragEvent) => {
      event.preventDefault();
      setDropTarget(undefined);
      const item = droppedItem(event);
      if (item !== null) {
        onDrop(item, folderId);
      }
    },
  });

  const rowClass = (folderId: string | null) =>
    `flex h-8 w-full cursor-pointer items-center gap-1.5 rounded-xs border-l-2 pr-2 text-left text-[17px] ${
      openId === folderId
        ? "border-copper bg-[#2a1c13] text-ink-bright font-semibold"
        : "border-transparent text-ink hover:bg-[#1e1813]"
    } ${dropTarget === folderId ? "ring-gold ring-1" : ""}`;

  const renderLevel = (parentId: string | null, depth: number) =>
    childrenOf(folders, parentId).map((folder) => {
      const hasChildren = folders.some((f) => f.parentId === folder.id);
      const isOpen = props.expanded.has(folder.id);
      return (
        <li key={folder.id}>
          <div
            role="button"
            tabIndex={0}
            draggable={props.renamingId !== folder.id}
            onDragStart={(event) => startDrag(event, { kind: "folder", id: folder.id })}
            onClick={() => onOpen(folder.id)}
            onKeyDown={(event) => event.key === "Enter" && onOpen(folder.id)}
            className={`${rowClass(folder.id)} ${INDENT[Math.min(depth, INDENT.length - 1)]}`}
            {...dropProps(folder.id)}
          >
            <button
              type="button"
              aria-label={isOpen ? text.collapse : text.expand}
              aria-expanded={isOpen}
              disabled={!hasChildren}
              onClick={(event) => {
                event.stopPropagation();
                props.onToggle(folder.id);
              }}
              className="text-copper w-3 shrink-0 cursor-pointer text-[10px] disabled:invisible"
            >
              {isOpen ? "▾" : "▸"}
            </button>
            {props.renamingId === folder.id ? (
              <InlineName
                initial={folder.name}
                label={text.folderNameLabel}
                maxLength={FOLDER_NAME_MAX}
                onSubmit={(name) => props.onRename(folder.id, name)}
                onCancel={props.onRenameEnd}
                className="h-6 min-w-0 flex-1 text-[15px]"
              />
            ) : (
              <span className="min-w-0 flex-1 truncate">{folder.name}</span>
            )}
            <span className="text-ink-faint text-sm italic">{counts.get(folder.id) ?? 0}</span>
          </div>
          {isOpen && hasChildren && <ul>{renderLevel(folder.id, depth + 1)}</ul>}
        </li>
      );
    });

  return (
    <nav
      aria-label={text.folders}
      className="border-line flex min-h-0 flex-col rounded-xs border p-2"
    >
      <p className="font-display text-gold mb-2 px-2 text-[10px] font-bold tracking-[2px]">
        {text.folders}
      </p>
      <ul className="min-h-0 flex-1 overflow-y-auto">
        <li>
          <button
            type="button"
            onClick={() => onOpen(null)}
            className={`${rowClass(null)} pl-2`}
            {...dropProps(null)}
          >
            <span className="flex-1">{text.allImages}</span>
            <span className="text-ink-faint text-sm italic">{images.length}</span>
          </button>
        </li>
        {renderLevel(null, 0)}
      </ul>
    </nav>
  );
}
