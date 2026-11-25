/** Ligne d'un morceau : vignette, titre, chaîne, durée et actions. */
import type { ReactNode } from "react";

import type { Track } from "../model";
import { formatDuration } from "../sync";

interface TrackRowProps {
  readonly track: Track;
  readonly children: ReactNode;
}

/** Vignette servie par YouTube ; seul ce domaine est autorisé en plus du stockage. */
export function TrackThumbnail({ videoId, className }: { videoId: string; className: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element -- vignette externe, sans optimisation
    <img
      src={`https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`}
      alt=""
      loading="lazy"
      draggable={false}
      className={`bg-field shrink-0 object-cover ${className}`}
    />
  );
}

export function TrackRow({ track, children }: TrackRowProps) {
  return (
    <li className="border-line flex items-center gap-3 rounded-xs border p-2">
      <TrackThumbnail videoId={track.videoId} className="h-[45px] w-[80px]" />
      <div className="min-w-0 flex-1">
        <p className="text-ink truncate text-[16px] leading-5" title={track.title}>
          {track.title}
        </p>
        <p className="text-ink-muted truncate text-sm italic">
          {track.channel} · {formatDuration(track.durationSeconds)}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">{children}</div>
      </div>
    </li>
  );
}
