/** File d'attente du MJ, que les joueurs ne voient pas. */
import { fill, labels } from "@/shared/i18n";

import { clearQueue, moveQueued, playQueued, removeQueued } from "../api";
import type { ListedTrack } from "../model";
import type { Act } from "../useMusicTool";
import { EMPTY, HEADING, LINK, LIST, PANEL } from "./styles";
import { TrackRow } from "./TrackRow";

interface QueuePanelProps {
  readonly queue: readonly ListedTrack[];
  readonly act: Act;
  readonly onClear: (confirmed: () => void) => void;
}

export function QueuePanel({ queue, act, onClear }: QueuePanelProps) {
  const text = labels.musicTool;

  return (
    <section aria-label={text.queue} className={PANEL}>
      <div className="flex items-center justify-between gap-3">
        <h2 className={HEADING}>{fill(text.queueTitle, { count: queue.length })}</h2>
        <button
          type="button"
          disabled={queue.length === 0}
          onClick={() => onClear(() => void act(clearQueue))}
          className={`${LINK} text-danger`}
        >
          {text.clearQueue}
        </button>
      </div>
      <ul className={LIST}>
        {queue.length === 0 && <li className={EMPTY}>{text.queueEmpty}</li>}
        {queue.map((item, index) => (
          <TrackRow key={item.id} track={item.track}>
            <button
              type="button"
              onClick={() => void act(() => playQueued(item.id))}
              className={`${LINK} text-gold`}
            >
              {text.broadcast}
            </button>
            <button
              type="button"
              disabled={index === 0}
              aria-label={text.moveUp}
              onClick={() => void act(() => moveQueued(item.id, index - 1))}
              className={`${LINK} text-ink-muted`}
            >
              ▲
            </button>
            <button
              type="button"
              disabled={index === queue.length - 1}
              aria-label={text.moveDown}
              onClick={() => void act(() => moveQueued(item.id, index + 1))}
              className={`${LINK} text-ink-muted`}
            >
              ▼
            </button>
            <button
              type="button"
              onClick={() => void act(() => removeQueued(item.id))}
              className={`${LINK} text-danger`}
            >
              {text.remove}
            </button>
          </TrackRow>
        ))}
      </ul>
    </section>
  );
}
