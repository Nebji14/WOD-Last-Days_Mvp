import { describe, expect, it } from "vitest";

import type { ChatMessage } from "./api";
import { buildTimeline, dayLabel } from "./timeline";

const NOW = new Date(2026, 10, 16, 21, 0);

function message(id: string, sentAt: Date): ChatMessage {
  return {
    id,
    position: Number(id),
    author: { id: "a1", displayName: "lea.vale", role: "player" },
    body: "…",
    sentAt: sentAt.toISOString(),
    edited: false,
    deletedBy: null,
    roll: null,
  };
}

describe("dayLabel", () => {
  it("nomme aujourd'hui et hier", () => {
    expect(dayLabel(new Date(2026, 10, 16, 0, 5), NOW)).toBe("AUJOURD'HUI");
    expect(dayLabel(new Date(2026, 10, 15, 23, 55), NOW)).toBe("HIER");
  });

  it("donne la date en toutes lettres pour un jour plus ancien", () => {
    expect(dayLabel(new Date(2026, 10, 3, 12, 0), NOW)).toBe("3 NOVEMBRE 2026");
  });
});

describe("buildTimeline", () => {
  it("intercale un séparateur avant le premier message de chaque jour", () => {
    const items = buildTimeline(
      [
        message("1", new Date(2026, 10, 15, 20, 0)),
        message("2", new Date(2026, 10, 15, 22, 0)),
        message("3", new Date(2026, 10, 16, 9, 0)),
      ],
      NOW,
    );

    expect(items.map((item) => (item.kind === "day" ? item.label : item.message.id))).toEqual([
      "HIER",
      "1",
      "2",
      "AUJOURD'HUI",
      "3",
    ]);
  });

  it("ne produit rien pour un historique vide", () => {
    expect(buildTimeline([], NOW)).toEqual([]);
  });
});
