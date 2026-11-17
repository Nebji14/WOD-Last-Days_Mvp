/** Pastille et libellé de présence d'un joueur : « En ligne » / « Hors ligne » (US-025 · CA2). */
import { labels } from "@/shared/i18n";

interface PresenceStatusProps {
  readonly online: boolean;
  /** Texte affiché quand le joueur est en ligne, s'il diffère du libellé court. */
  readonly onlineText?: string;
}

export function PresenceStatus({ online, onlineText }: PresenceStatusProps) {
  const text = labels.playersTool;
  return (
    <span className="text-ink-muted flex shrink-0 items-center gap-2 text-[15px] italic">
      <span
        aria-hidden="true"
        className={`size-2 rounded-full ${online ? "bg-online" : "bg-ink-faint"}`}
      />
      {online ? (onlineText ?? text.online) : text.offline}
    </span>
  );
}
