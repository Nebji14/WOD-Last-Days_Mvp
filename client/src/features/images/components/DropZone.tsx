"use client";

/**
 * [Zone de glisser-déposer] (04b-I1) : toujours visible sous la grille. Les
 * fichiers déposés vont dans le dossier ouvert. Au survol d'un fichier glissé :
 * bordure pleine or, fond plus clair. Une barre de progression par fichier ;
 * un fichier refusé affiche la raison.
 */
import { type DragEvent, useState } from "react";

import { errorLabel, fill, labels } from "@/shared/i18n";

import type { UploadProgress } from "../useImageLibrary";
import { carriesItem } from "./dragData";

interface DropZoneProps {
  readonly uploads: readonly UploadProgress[];
  readonly onFiles: (files: File[]) => void;
  readonly onDismiss: (key: string) => void;
}

/** Un glisser venu de l'ordinateur porte des fichiers, pas un élément de la bibliothèque. */
function carriesFiles(event: DragEvent): boolean {
  return !carriesItem(event) && Array.from(event.dataTransfer.types).includes("Files");
}

export function DropZone({ uploads, onFiles, onDismiss }: DropZoneProps) {
  const text = labels.imagesTool;
  const [hovered, setHovered] = useState(false);

  return (
    <div className="flex flex-col gap-2">
      <div
        onDragOver={(event) => {
          if (carriesFiles(event)) {
            event.preventDefault();
            setHovered(true);
          }
        }}
        onDragLeave={() => setHovered(false)}
        onDrop={(event) => {
          if (!carriesFiles(event)) {
            return;
          }
          event.preventDefault();
          setHovered(false);
          onFiles(Array.from(event.dataTransfer.files));
        }}
        className={`flex h-[150px] shrink-0 flex-col items-center justify-center gap-2 rounded-sm border-2 transition-colors ${
          hovered ? "border-gold border-solid bg-[#211a14]" : "border-gold/60 border-dashed"
        }`}
      >
        <svg
          viewBox="0 0 40 40"
          aria-hidden="true"
          className="text-gold size-10"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M20 26V6M12 14l8-8 8 8M6 26v8h28v-8" />
        </svg>
        <p className="font-display text-gold text-[15px] font-bold tracking-[3px]">
          {text.dropTitle}
        </p>
        <p className="text-ink-muted text-[15px] italic">{text.dropHint}</p>
      </div>
      {uploads.length > 0 && (
        <ul className="flex flex-col gap-1.5" aria-live="polite">
          {uploads.map((upload) => (
            <li key={upload.key} className="flex items-center gap-3 text-[15px]">
              {upload.errorCode === null ? (
                <>
                  <span className="text-ink-muted w-56 truncate italic">
                    {fill(text.uploading, { name: upload.name })}
                  </span>
                  <progress
                    value={upload.progress}
                    max={1}
                    className="accent-gold h-1.5 flex-1"
                    aria-label={upload.name}
                  />
                </>
              ) : (
                <>
                  <span role="alert" className="text-danger flex-1">
                    {fill(text.uploadFailed, {
                      name: upload.name,
                      reason: errorLabel(upload.errorCode),
                    })}
                  </span>
                  <button
                    type="button"
                    aria-label={labels.imagesTool.close}
                    onClick={() => onDismiss(upload.key)}
                    className="text-ink-muted cursor-pointer px-1"
                  >
                    ✕
                  </button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
