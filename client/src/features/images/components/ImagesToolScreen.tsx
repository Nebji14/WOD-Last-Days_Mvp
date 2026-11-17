"use client";

/**
 * Fenêtre de l'outil Images du MJ : bibliothèque à gauche, images posées sur la
 * table à droite. Le serveur refuse la bibliothèque à tout autre compte.
 */
import { useEffect, useState } from "react";

import { errorLabel, labels } from "@/shared/i18n";
import { DetachedTitleBar } from "@/shared/ui/DetachedTitleBar";

import { putDownImage, removeFromTable } from "../api";
import { useImageLibrary } from "../useImageLibrary";
import { LibraryPanel } from "./LibraryPanel";
import { OnTablePanel } from "./OnTablePanel";

const MESSAGE = "text-ink-muted flex flex-1 items-center justify-center p-8 text-xl italic";
const ERROR_DURATION_MS = 6000;

export function ImagesToolScreen() {
  const state = useImageLibrary();
  const { library, scene, act } = state;
  const text = labels.imagesTool;
  const [localError, setLocalError] = useState<string | null>(null);
  const errorCode = localError ?? state.errorCode;

  useEffect(() => {
    document.title = text.windowTitle;
  }, [text.windowTitle]);

  useEffect(() => {
    if (localError === null) {
      return;
    }
    const timer = window.setTimeout(() => setLocalError(null), ERROR_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [localError]);

  return (
    <div className="bg-night text-ink flex h-screen flex-col">
      <DetachedTitleBar title={text.windowTitle} subtitle={text.subtitle} closeLabel={text.close} />
      {errorCode !== null && (
        <p
          role="alert"
          className="border-blood-line bg-danger-panel text-danger-bright shrink-0 border-b px-8 py-2 text-[15px]"
        >
          {errorLabel(errorCode)}
        </p>
      )}
      {library === null ? (
        <main className={MESSAGE}>{text.loading}</main>
      ) : (
        <main className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_290px] gap-6 p-8">
          <LibraryPanel {...state} library={library} onLocalError={setLocalError} />
          <OnTablePanel
            scene={scene}
            onPutDown={() => void act(putDownImage)}
            onRemove={(imageId) => void act(() => removeFromTable(imageId))}
          />
        </main>
      )}
    </div>
  );
}
