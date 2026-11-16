/**
 * Signalement de l'état de la connexion temps réel.
 *
 * - Coupure : bandeau discret, la reconnexion est automatique (03-E7, CDC 12.3).
 * - Table complète : les neuf places sont prises (CDC 12.3), la table n'est pas
 *   affichée.
 */
import type { RealtimeStatus } from "@/shared/realtime/client";
import { labels } from "@/shared/i18n";

interface ConnectionNoticeProps {
  readonly status: RealtimeStatus;
}

export function ConnectionNotice({ status }: ConnectionNoticeProps) {
  const text = labels.table.connection;

  if (status === "reconnecting") {
    return (
      <p
        role="status"
        className="border-danger text-danger-bright bg-danger-panel absolute top-[72px] left-8 z-30 rounded-xs border px-4 py-1.5 text-[15px] font-medium italic"
      >
        {text.reconnecting}
      </p>
    );
  }
  if (status === "table_full") {
    return (
      <div
        role="alert"
        className="absolute inset-0 top-16 z-30 flex flex-col items-center justify-center gap-3 bg-[rgb(7_4_4/0.9)]"
      >
        <p className="font-display text-gold text-lg font-bold tracking-[4px]">{text.fullTitle}</p>
        <p className="text-ink text-xl font-medium">{text.fullMessage}</p>
      </div>
    );
  }
  return null;
}
