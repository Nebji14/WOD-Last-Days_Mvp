"use client";

/**
 * Musique de la table, pour tous.
 *
 * Le navigateur exige un clic avant de jouer du son : chacun l'active une fois.
 * Le lecteur vit hors de la scène mise à l'échelle, car il doit garder une taille
 * minimale et rester visible, sans rien devant lui. Couper le son le retire.
 * Côté joueur, l'encart est réduit et n'annonce pas le morceau. Quand le MJ
 * montre la vidéo, le même lecteur passe en grand : rien n'est rechargé.
 */
import { useEffect, useRef, useState } from "react";

import { labels } from "@/shared/i18n";
import type { RealtimeClient } from "@/shared/realtime/client";

import { skipTrack } from "../api";
import type { HeardMusic } from "../model";
import { useDrag } from "../useDrag";
import { useMusicPlayer } from "../useMusicPlayer";
import { useTableMusic } from "../useTableMusic";
import { readVolume, saveVolume } from "../volume";

const PANEL =
  "border-line bg-panel text-ink fixed z-[70] max-w-[calc(100vw-32px)] rounded-md border shadow-[0_8px_32px_rgb(0_0_0/0.6)]";
/** Vidéo en grand au centre ; la largeur suit la hauteur pour ne pas déborder. */
const LARGE =
  "inset-0 m-auto h-fit min-w-[202px] w-[min(960px,calc(100vw-32px),calc((100vh-200px)*16/9))]";
const ACTION =
  "font-display text-ink flex-1 cursor-pointer rounded-xs border px-2 py-1.5 text-[10px] font-bold tracking-[2px] hover:brightness-125";

interface TableMusicProps {
  readonly realtime: RealtimeClient | null;
  readonly isGm: boolean;
}

export function TableMusic({ realtime, isGm }: TableMusicProps) {
  const heard = useTableMusic(realtime);
  const [enabled, setEnabled] = useState(false);

  if (heard === null || heard.now.track === null) {
    return null;
  }
  // Le bouton des dés du MJ occupe le coin en bas à gauche. La largeur du joueur
  // laisse au lecteur ses 200 pixels minimum, bordures déduites.
  const corner = isGm ? "bottom-20 left-4 w-[256px]" : "bottom-4 left-4 w-[202px]";
  const { videoShown, track } = heard.now;
  const text = labels.tableMusic;
  const title = isGm ? track.title : videoShown ? text.videoTitle : text.discreetTitle;
  if (!enabled) {
    return (
      <SoundOff
        title={title}
        action={videoShown ? text.watch : text.enable}
        corner={corner}
        onEnable={() => setEnabled(true)}
      />
    );
  }
  return (
    <Player
      heard={heard}
      title={title}
      corner={corner}
      isGm={isGm}
      onDisable={() => setEnabled(false)}
    />
  );
}

interface SoundOffProps {
  readonly title: string;
  readonly action: string;
  readonly corner: string;
  readonly onEnable: () => void;
}

function SoundOff({ title, action, corner, onEnable }: SoundOffProps) {
  const text = labels.tableMusic;

  return (
    <aside aria-label={text.label} className={`${PANEL} ${corner} flex flex-col gap-2 p-3`}>
      <p className="truncate text-[16px]" title={title}>
        <span aria-hidden="true" className="text-gold">
          ♪{" "}
        </span>
        {title}
      </p>
      <button type="button" onClick={onEnable} className={`${ACTION} border-gold`}>
        {action}
      </button>
    </aside>
  );
}

interface PlayerProps {
  readonly heard: HeardMusic;
  readonly title: string;
  readonly corner: string;
  readonly isGm: boolean;
  readonly onDisable: () => void;
}

function Player({ heard, title, corner, isGm, onDisable }: PlayerProps) {
  const text = labels.tableMusic;
  const panel = useRef<HTMLElement>(null);
  const container = useRef<HTMLDivElement>(null);
  const [volume, setVolume] = useState(readVolume);
  const [paused, setPaused] = useState(false);
  const { handlers, reset } = useDrag(panel);
  const large = heard.now.videoShown;
  const failed = useMusicPlayer({
    container,
    heard,
    volume,
    paused,
    // Le MJ passe le morceau pour tous ; le serveur refuserait un joueur.
    onUnplayable: (playId) => {
      if (isGm) {
        skipTrack(playId).catch((error: unknown) => console.warn("Morceau non passé", error));
      }
    },
  });

  // Chaque format a sa place : le déplacement de l'un ne décale pas l'autre.
  useEffect(reset, [large, reset]);

  return (
    <aside
      ref={panel}
      aria-label={text.label}
      className={`${PANEL} ${large ? LARGE : corner}`}
    >
      <p
        {...handlers}
        title={`${title} · ${text.move}`}
        className="cursor-move touch-none truncate px-3 py-1.5 text-[15px] select-none"
      >
        <span aria-hidden="true" className="text-gold">
          ♪{" "}
        </span>
        {title}
      </p>
      <div
        ref={container}
        className={`min-h-[200px] w-full bg-black [&>iframe]:size-full ${
          large ? "aspect-video" : "h-[200px]"
        }`}
      />
      {failed && (
        <p role="status" className="text-danger px-3 pt-2 text-sm italic">
          {text.failed}
        </p>
      )}
      <div className="flex flex-col gap-2 px-3 py-2">
        <input
          type="range"
          min={0}
          max={100}
          value={volume}
          aria-label={text.volume}
          onChange={(event) => {
            const next = Number(event.target.value);
            setVolume(next);
            saveVolume(next);
          }}
          className="accent-gold w-full min-w-0"
        />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPaused(!paused)}
            className={`${ACTION} border-line-strong`}
          >
            {paused ? text.resume : text.pause}
          </button>
          <button type="button" onClick={onDisable} className={`${ACTION} border-line-strong`}>
            {text.disable}
          </button>
        </div>
      </div>
    </aside>
  );
}
