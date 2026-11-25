"use client";

/** Playlists enregistrées : création, lecture, renommage et suppression. */
import { type FormEvent, useState } from "react";

import { fill, labels } from "@/shared/i18n";
import { InlineName } from "@/shared/ui/InlineName";

import { createPlaylist, playPlaylist, removeFromPlaylist, renamePlaylist } from "../api";
import type { ListedTrack, Playlist } from "../model";
import type { Act } from "../useMusicTool";
import { BUTTON, EMPTY, FIELD, HEADING, LINK, LIST, PANEL } from "./styles";
import { TrackRow } from "./TrackRow";

const NAME_MAX = 60;

interface PlaylistsPanelProps {
  readonly playlists: readonly Playlist[];
  readonly act: Act;
  readonly onDelete: (playlist: Playlist) => void;
  readonly onRemoveTrack: (entry: ListedTrack, confirmed: () => void) => void;
}

export function PlaylistsPanel(props: PlaylistsPanelProps) {
  const { playlists, act } = props;
  const text = labels.musicTool;
  const [name, setName] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);

  async function create(event: FormEvent): Promise<void> {
    event.preventDefault();
    const wanted = name.trim();
    if (wanted !== "" && (await act(() => createPlaylist(wanted)))) {
      setName("");
    }
  }

  return (
    <section aria-label={text.playlists} className={PANEL}>
      <h2 className={HEADING}>{text.playlists}</h2>
      <form onSubmit={(event) => void create(event)} className="flex gap-2">
        <input
          type="text"
          value={name}
          maxLength={NAME_MAX}
          aria-label={text.playlistName}
          placeholder={text.playlistPlaceholder}
          onChange={(event) => setName(event.target.value)}
          className={`${FIELD} flex-1`}
        />
        <button type="submit" disabled={name.trim() === ""} className={BUTTON}>
          {text.create}
        </button>
      </form>
      <ul className={LIST}>
        {playlists.length === 0 && <li className={EMPTY}>{text.playlistsEmpty}</li>}
        {playlists.map((playlist) => (
          <PlaylistItem
            key={playlist.id}
            {...props}
            playlist={playlist}
            open={openId === playlist.id}
            onToggle={() => setOpenId(openId === playlist.id ? null : playlist.id)}
          />
        ))}
      </ul>
    </section>
  );
}

interface PlaylistItemProps extends PlaylistsPanelProps {
  readonly playlist: Playlist;
  readonly open: boolean;
  readonly onToggle: () => void;
}

function PlaylistItem(props: PlaylistItemProps) {
  const { playlist, open, act } = props;
  const text = labels.musicTool;
  const [renaming, setRenaming] = useState(false);
  const empty = playlist.tracks.length === 0;

  return (
    <li className="border-line flex flex-col gap-2 rounded-xs border p-2.5">
      {renaming ? (
        <InlineName
          initial={playlist.name}
          label={text.playlistName}
          maxLength={NAME_MAX}
          onSubmit={(name) => {
            setRenaming(false);
            void act(() => renamePlaylist(playlist.id, name));
          }}
          onCancel={() => setRenaming(false)}
          className="h-8 text-[17px]"
        />
      ) : (
        <button
          type="button"
          aria-expanded={open}
          onClick={props.onToggle}
          className="flex cursor-pointer items-baseline justify-between gap-3 text-left"
        >
          <span className="text-ink-bright truncate text-[17px]">{playlist.name}</span>
          <span className="text-ink-muted shrink-0 text-sm italic">
            {fill(text.trackCount, { count: playlist.tracks.length })}
          </span>
        </button>
      )}
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        <button
          type="button"
          disabled={empty}
          onClick={() => void act(() => playPlaylist(playlist.id, false))}
          className={`${LINK} text-gold`}
        >
          {text.broadcast}
        </button>
        <button
          type="button"
          disabled={empty}
          onClick={() => void act(() => playPlaylist(playlist.id, true))}
          className={`${LINK} text-gold`}
        >
          {text.shuffle}
        </button>
        <button
          type="button"
          onClick={() => setRenaming(true)}
          className={`${LINK} text-copper-light`}
        >
          {text.rename}
        </button>
        <button
          type="button"
          onClick={() => props.onDelete(playlist)}
          className={`${LINK} text-danger`}
        >
          {text.delete}
        </button>
      </div>
      {open && (
        <ul className="flex flex-col gap-2">
          {empty && <li className={EMPTY}>{text.playlistEmpty}</li>}
          {playlist.tracks.map((entry) => (
            <TrackRow key={entry.id} track={entry.track}>
              <button
                type="button"
                onClick={() =>
                  props.onRemoveTrack(
                    entry,
                    () => void act(() => removeFromPlaylist(playlist.id, entry.id)),
                  )
                }
                className={`${LINK} text-danger`}
              >
                {text.remove}
              </button>
            </TrackRow>
          ))}
        </ul>
      )}
    </li>
  );
}
