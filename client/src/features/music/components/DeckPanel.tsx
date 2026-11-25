"use client";

/** Lecture en cours et commandes du MJ, appliquées à toute la table. */
import { useEffect, useState } from "react";

import { labels } from "@/shared/i18n";

import {
  pauseMusic,
  resumeMusic,
  seekMusic,
  setRepeat,
  showVideo,
  skipTrack,
  stopMusic,
} from "../api";
import { type Deck, type HeardMusic, REPEAT_MODES, type RepeatMode } from "../model";
import { expectedPosition, formatDuration } from "../sync";
import type { Act } from "../useMusicTool";
import { BUTTON, EMPTY, HEADING, PRIMARY } from "./styles";
import { TrackThumbnail } from "./TrackRow";

const TICK_MS = 500;

interface DeckPanelProps {
  readonly deck: Deck;
  readonly heard: HeardMusic;
  readonly act: Act;
}

export function DeckPanel({ deck, heard, act }: DeckPanelProps) {
  const text = labels.musicTool;
  const { now } = deck;
  const { track } = now;

  return (
    <section
      aria-label={text.nowPlaying}
      className="border-line bg-panel flex shrink-0 flex-wrap items-center gap-x-6 gap-y-3 rounded-xs border px-4 py-4"
    >
      <div className="flex min-w-0 flex-1 basis-[320px] items-center gap-4">
        {track !== null && (
          <TrackThumbnail videoId={track.videoId} className="h-[68px] w-[120px]" />
        )}
        <div className="min-w-0 flex-1">
          <h2 className={HEADING}>{now.playing ? text.nowPlaying : text.nowPaused}</h2>
          {track === null ? (
            <p className={EMPTY}>{text.nothingPlaying}</p>
          ) : (
            <>
              <p className="text-ink-bright truncate text-xl" title={track.title}>
                {track.title}
              </p>
              <SeekBar
                key={now.playId}
                heard={heard}
                duration={track.durationSeconds}
                onSeek={(seconds) => void act(() => seekMusic(seconds))}
              />
            </>
          )}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={track === null}
          onClick={() => void act(now.playing ? pauseMusic : resumeMusic)}
          className={PRIMARY}
        >
          {now.playing ? text.pause : text.resume}
        </button>
        <button
          type="button"
          disabled={track === null}
          onClick={() => void act(() => skipTrack(now.playId))}
          className={BUTTON}
        >
          {text.next}
        </button>
        <button
          type="button"
          disabled={track === null}
          onClick={() => void act(stopMusic)}
          className={BUTTON}
        >
          {text.stop}
        </button>
        <button
          type="button"
          disabled={track === null}
          aria-pressed={now.videoShown}
          onClick={() => void act(() => showVideo(!now.videoShown))}
          className={BUTTON}
        >
          {now.videoShown ? text.hideVideo : text.showVideo}
        </button>
        <label className="text-ink-muted flex items-center gap-2 text-[15px]">
          {text.repeat}
          <select
            value={deck.repeat}
            onChange={(event) => {
              const mode = event.target.value as RepeatMode;
              void act(() => setRepeat(mode));
            }}
            className="border-line bg-field text-ink h-9 rounded-xs border px-2"
          >
            {REPEAT_MODES.map((mode) => (
              <option key={mode} value={mode}>
                {text.repeatModes[mode]}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}

interface SeekBarProps {
  readonly heard: HeardMusic;
  readonly duration: number;
  readonly onSeek: (seconds: number) => void;
}

/** Barre de position. Rien n'est envoyé avant le relâchement du curseur. */
function SeekBar({ heard, duration, onSeek }: SeekBarProps) {
  const [clock, setClock] = useState(() => performance.now());
  const [draft, setDraft] = useState<number | null>(null);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(performance.now()), TICK_MS);
    return () => window.clearInterval(timer);
  }, []);

  const position = draft ?? expectedPosition(heard, clock);
  const commit = () => {
    if (draft !== null) {
      onSeek(draft);
      setDraft(null);
    }
  };

  return (
    <div className="text-ink-muted flex items-center gap-3 text-sm">
      <span className="w-12 tabular-nums">{formatDuration(position)}</span>
      <input
        type="range"
        min={0}
        max={duration}
        value={Math.floor(position)}
        aria-label={labels.musicTool.position}
        aria-valuetext={formatDuration(position)}
        onChange={(event) => setDraft(Number(event.target.value))}
        onPointerUp={commit}
        onKeyUp={commit}
        onBlur={commit}
        className="accent-gold min-w-0 flex-1"
      />
      <span className="w-12 text-right tabular-nums">{formatDuration(duration)}</span>
    </div>
  );
}
