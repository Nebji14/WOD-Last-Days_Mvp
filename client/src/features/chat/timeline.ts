/**
 * Mise en forme de l'historique du chat : séparateurs de jour (08b,
 * [Historique des messages]).
 */
import { longDate } from "@/shared/format/date";
import { labels } from "@/shared/i18n";

import type { ChatMessage } from "./api";

export type TimelineItem =
  | { readonly kind: "day"; readonly key: string; readonly label: string }
  | { readonly kind: "message"; readonly key: string; readonly message: ChatMessage };

function dayKey(date: Date): string {
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
}

/** Libellé d'un jour : « AUJOURD'HUI », « HIER », sinon la date en toutes lettres. */
export function dayLabel(date: Date, now: Date): string {
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (dayKey(date) === dayKey(now)) {
    return labels.chat.today;
  }
  if (dayKey(date) === dayKey(yesterday)) {
    return labels.chat.yesterday;
  }
  return longDate(date).toUpperCase();
}

/** Intercale un séparateur avant le premier message de chaque jour. */
export function buildTimeline(messages: readonly ChatMessage[], now: Date): TimelineItem[] {
  const items: TimelineItem[] = [];
  let previousDay = "";
  for (const message of messages) {
    const sentAt = new Date(message.sentAt);
    const key = dayKey(sentAt);
    if (key !== previousDay) {
      items.push({ kind: "day", key: `day-${key}`, label: dayLabel(sentAt, now) });
      previousDay = key;
    }
    items.push({ kind: "message", key: message.id, message });
  }
  return items;
}
