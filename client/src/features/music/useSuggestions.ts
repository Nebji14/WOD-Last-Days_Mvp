"use client";

/** Suggestions d'une saisie en cours ; le serveur n'est interrogé qu'à chaque pause de frappe. */
import { useEffect, useMemo, useState } from "react";

import { labels } from "@/shared/i18n";

import { fetchSuggestions } from "./api";
import type { Playlist } from "./model";
import { buildSuggestions, isLink } from "./suggestions";

const TYPING_PAUSE_MS = 400;
const MIN_LENGTH = 3;
const MAX_LENGTH = 80;
const NO_REMOTE = { query: "", items: [] as readonly string[] };

export function useSuggestions(
  query: string,
  recent: readonly string[],
  playlists: readonly Playlist[],
): readonly string[] {
  const [remote, setRemote] = useState(NO_REMOTE);
  const wanted = query.trim();

  useEffect(() => {
    if (wanted.length < MIN_LENGTH || wanted.length > MAX_LENGTH || isLink(wanted)) {
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      fetchSuggestions(wanted)
        .then((items) => {
          if (!cancelled) {
            setRemote({ query: wanted, items });
          }
        })
        .catch((error: unknown) => console.warn("Suggestions indisponibles", error));
    }, TYPING_PAUSE_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [wanted]);

  return useMemo(
    () =>
      buildSuggestions(wanted, {
        recent,
        ambiances: labels.musicTool.ambiances,
        playlistTitles: playlists.flatMap((list) => list.tracks.map((item) => item.track.title)),
        remote,
      }),
    [wanted, recent, playlists, remote],
  );
}
