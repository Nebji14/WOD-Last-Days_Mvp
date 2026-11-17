"use client";

/**
 * État de l'outil Images du MJ (écran 04b).
 *
 * - La bibliothèque et la scène de la table se relisent à chaque changement
 *   signalé par le serveur (≤ 1 s, CDC 12.3), et régulièrement pour renouveler
 *   les liens signés avant leur expiration.
 * - Les envois de fichiers partent en parallèle, chacun avec sa progression ;
 *   un fichier refusé affiche la raison sans bloquer les autres (04b-I1).
 * - Sans session, la fenêtre se ferme (T3).
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/shared/api/client";
import { useDetachedRealtime } from "@/shared/realtime/useDetachedRealtime";

import { fetchLibrary, fetchScene, type Library, type TableScene, uploadImage } from "./api";

/** Les liens signés vivent 2 h : la bibliothèque est relue bien avant. */
const LINK_REFRESH_MS = 30 * 60 * 1000;

export interface UploadProgress {
  readonly key: string;
  readonly name: string;
  /** Part envoyée, de 0 à 1. */
  readonly progress: number;
  /** Code d'erreur si le fichier a été refusé. */
  readonly errorCode: string | null;
}

export interface ImageLibraryState {
  readonly library: Library | null;
  readonly scene: TableScene;
  readonly uploads: readonly UploadProgress[];
  readonly errorCode: string | null;
  /** Lance une action, signale son éventuel échec, puis relit la bibliothèque. */
  readonly act: (action: () => Promise<unknown>) => Promise<boolean>;
  readonly upload: (files: readonly File[], folderId: string | null) => void;
  readonly dismissUpload: (key: string) => void;
}

const EMPTY_SCENE: TableScene = { shown: null, pile: [] };

function codeOf(error: unknown): string {
  return error instanceof ApiError ? error.code : "internal_error";
}

export function useImageLibrary(): ImageLibraryState {
  const [library, setLibrary] = useState<Library | null>(null);
  const [scene, setScene] = useState<TableScene>(EMPTY_SCENE);
  const [uploads, setUploads] = useState<readonly UploadProgress[]>([]);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const mountedRef = useRef(true);
  const uploadCounter = useRef(0);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const fail = useCallback((error: unknown) => {
    if (error instanceof ApiError && error.status === 401) {
      window.close();
    } else if (mountedRef.current) {
      setErrorCode(codeOf(error));
    }
  }, []);

  const reload = useCallback(async (): Promise<void> => {
    try {
      const [nextLibrary, nextScene] = await Promise.all([fetchLibrary(), fetchScene()]);
      if (mountedRef.current) {
        setLibrary(nextLibrary);
        setScene(nextScene);
      }
    } catch (error) {
      fail(error);
    }
  }, [fail]);

  useDetachedRealtime("images.changed", useCallback(() => void reload(), [reload]));

  useEffect(() => {
    const timer = window.setInterval(() => void reload(), LINK_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [reload]);

  const act = useCallback(
    async (action: () => Promise<unknown>): Promise<boolean> => {
      setErrorCode(null);
      try {
        await action();
        await reload();
        return true;
      } catch (error) {
        fail(error);
        return false;
      }
    },
    [fail, reload],
  );

  const patchUpload = useCallback((key: string, change: Partial<UploadProgress>) => {
    if (mountedRef.current) {
      setUploads((current) => current.map((u) => (u.key === key ? { ...u, ...change } : u)));
    }
  }, []);

  const upload = useCallback(
    (files: readonly File[], folderId: string | null) => {
      for (const file of files) {
        uploadCounter.current += 1;
        const key = `upload-${uploadCounter.current}`;
        setUploads((current) => [...current, { key, name: file.name, progress: 0, errorCode: null }]);
        uploadImage(file, folderId, (progress) => patchUpload(key, { progress }))
          .then(() => {
            if (mountedRef.current) {
              setUploads((current) => current.filter((u) => u.key !== key));
            }
            return reload();
          })
          .catch((error: unknown) => patchUpload(key, { errorCode: codeOf(error) }));
      }
    },
    [patchUpload, reload],
  );

  const dismissUpload = useCallback((key: string) => {
    setUploads((current) => current.filter((u) => u.key !== key));
  }, []);

  return { library, scene, uploads, errorCode, act, upload, dismissUpload };
}
