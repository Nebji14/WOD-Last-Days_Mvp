"use client";

/**
 * Recherche de musique. Elle part sur validation ou sur le choix d'une
 * suggestion, pas à chaque frappe : le nombre de recherches par jour est limité.
 */
import { type FormEvent, useState } from "react";

import { ApiError } from "@/shared/api/client";
import { errorLabel, labels } from "@/shared/i18n";

import { addToPlaylist, enqueueTrack, playTrack, searchTracks } from "../api";
import type { Playlist, Track } from "../model";
import { isLink, readRecent, saveRecent, withRecent } from "../suggestions";
import type { Act } from "../useMusicTool";
import { useSuggestions } from "../useSuggestions";
import { EMPTY, HEADING, LINK, LIST, PANEL, PRIMARY } from "./styles";
import { SuggestionField } from "./SuggestionField";
import { TrackRow } from "./TrackRow";

const QUERY_MAX = 200;

interface SearchPanelProps {
  readonly playlists: readonly Playlist[];
  readonly act: Act;
}

export function SearchPanel({ playlists, act }: SearchPanelProps) {
  const text = labels.musicTool;
  const [query, setQuery] = useState("");
  const [tracks, setTracks] = useState<readonly Track[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [recent, setRecent] = useState(readRecent);
  const suggestions = useSuggestions(query, recent, playlists);

  async function search(asked: string): Promise<void> {
    const wanted = asked.trim();
    if (wanted === "" || busy) {
      return;
    }
    setBusy(true);
    setErrorCode(null);
    try {
      setTracks(await searchTracks(wanted));
      if (!isLink(wanted)) {
        const next = withRecent(recent, wanted);
        setRecent(next);
        saveRecent(next);
      }
    } catch (error) {
      setErrorCode(error instanceof ApiError ? error.code : "internal_error");
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent): void {
    event.preventDefault();
    void search(query);
  }

  return (
    <section aria-label={text.search} className={PANEL}>
      <h2 className={HEADING}>{text.search}</h2>
      <form role="search" onSubmit={submit} className="flex gap-2">
        <SuggestionField
          value={query}
          maxLength={QUERY_MAX}
          suggestions={suggestions}
          onChange={setQuery}
          onPick={(suggestion) => {
            setQuery(suggestion);
            void search(suggestion);
          }}
        />
        <button type="submit" disabled={busy} className={PRIMARY}>
          {busy ? text.searching : text.searchSubmit}
        </button>
      </form>
      {errorCode !== null && (
        <p role="alert" className="text-danger text-[15px]">
          {errorLabel(errorCode)}
        </p>
      )}
      <ul className={LIST}>
        {tracks === null && <li className={EMPTY}>{text.searchHint}</li>}
        {tracks?.length === 0 && <li className={EMPTY}>{text.noResult}</li>}
        {tracks?.map((track) => (
          <TrackRow key={track.videoId} track={track}>
            <button
              type="button"
              onClick={() => void act(() => playTrack(track.videoId, false))}
              className={`${LINK} text-gold`}
            >
              {text.broadcastSound}
            </button>
            <button
              type="button"
              onClick={() => void act(() => playTrack(track.videoId, true))}
              className={`${LINK} text-gold`}
            >
              {text.broadcastVideo}
            </button>
            <button
              type="button"
              onClick={() => void act(() => enqueueTrack(track.videoId))}
              className={`${LINK} text-copper-light`}
            >
              {text.enqueue}
            </button>
            {playlists.length > 0 && (
              <select
                value=""
                aria-label={text.addToPlaylist}
                onChange={(event) => {
                  const playlistId = event.target.value;
                  void act(() => addToPlaylist(playlistId, track.videoId));
                }}
                className="border-line bg-field text-ink-muted h-6 max-w-[150px] rounded-xs border text-[13px]"
              >
                <option value="" disabled>
                  {text.addToPlaylist}
                </option>
                {playlists.map((playlist) => (
                  <option key={playlist.id} value={playlist.id}>
                    {playlist.name}
                  </option>
                ))}
              </select>
            )}
          </TrackRow>
        ))}
      </ul>
    </section>
  );
}
