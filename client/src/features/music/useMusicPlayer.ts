"use client";

/**
 * Lecteur d'un participant, calé sur la lecture commune.
 *
 * Un participant peut se mettre en pause pour lui seul ; il reprend ensuite là où
 * en est la table.
 */
import { type RefObject, useEffect, useRef, useState } from "react";

import type { HeardMusic } from "./model";
import { expectedPosition, needsSeek } from "./sync";
import {
  mountPlayer,
  PLAYER_CUED,
  PLAYER_PLAYING,
  PLAYER_UNSTARTED,
  type YouTubePlayer,
} from "./youtubePlayer";

const CHECK_INTERVAL_MS = 3000;

/** Dernier état appliqué au lecteur. */
interface Applied {
  readonly playId: number;
  readonly audible: boolean;
}

interface MusicPlayerOptions {
  readonly container: RefObject<HTMLDivElement | null>;
  readonly heard: HeardMusic;
  /** Volume personnel, de 0 à 100. */
  readonly volume: number;
  /** Pause personnelle, sans effet sur les autres. */
  readonly paused: boolean;
  /** Le morceau de cette lecture ne se joue chez personne. */
  readonly onUnplayable: (playId: number) => void;
}

/** @returns `true` si le lecteur est en échec sur cet écran. */
export function useMusicPlayer(options: MusicPlayerOptions): boolean {
  const { container, heard, volume, paused, onUnplayable } = options;
  const [player, setPlayer] = useState<YouTubePlayer | null>(null);
  const [failedPlayId, setFailedPlayId] = useState<number | null>(null);
  const applied = useRef<Applied | null>(null);
  const latest = useRef({ heard, onUnplayable });

  useEffect(() => {
    latest.current = { heard, onUnplayable };
  }, [heard, onUnplayable]);

  useEffect(() => {
    const element = container.current;
    const track = latest.current.heard.now.track;
    if (element === null || track === null) {
      return;
    }
    const playId = (): number => latest.current.heard.now.playId;
    const unmount = mountPlayer(element, track.videoId, {
      onReady: setPlayer,
      onUnplayable: () => {
        setFailedPlayId(playId());
        latest.current.onUnplayable(playId());
      },
      onFailure: () => setFailedPlayId(playId()),
    });
    return () => {
      unmount();
      applied.current = null;
      setPlayer(null);
    };
  }, [container]);

  // Applique chaque commande du MJ, et la pause personnelle.
  useEffect(() => {
    const { now } = heard;
    if (player === null || now.track === null) {
      return;
    }
    const previous = applied.current;
    const audible = now.playing && !paused;
    const position = expectedPosition(heard, performance.now());
    if (previous === null || previous.playId !== now.playId) {
      const start = { videoId: now.track.videoId, startSeconds: position };
      if (audible) {
        player.loadVideoById(start);
      } else {
        player.cueVideoById(start);
      }
    } else if (!audible) {
      const state = player.getPlayerState();
      player.pauseVideo();
      // Se déplacer dans une vidéo jamais lancée la démarrerait.
      const started = state !== PLAYER_CUED && state !== PLAYER_UNSTARTED;
      if (started && needsSeek(player.getCurrentTime(), position)) {
        player.seekTo(position, true);
      }
    } else {
      if (needsSeek(player.getCurrentTime(), position)) {
        player.seekTo(position, true);
      }
      if (!previous.audible) {
        player.playVideo();
      }
    }
    applied.current = { playId: now.playId, audible };
  }, [heard, paused, player]);

  useEffect(() => {
    if (player !== null) {
      player.unMute();
      player.setVolume(volume);
    }
  }, [player, volume]);

  // Rattrape un lecteur en retard, après une publicité par exemple.
  useEffect(() => {
    if (player === null) {
      return;
    }
    const timer = window.setInterval(() => {
      const current = latest.current.heard;
      if (!current.now.playing || player.getPlayerState() !== PLAYER_PLAYING) {
        return;
      }
      const position = expectedPosition(current, performance.now());
      if (needsSeek(player.getCurrentTime(), position)) {
        player.seekTo(position, true);
      }
    }, CHECK_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [player]);

  return failedPlayId === heard.now.playId;
}
