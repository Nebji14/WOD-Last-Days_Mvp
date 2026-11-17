import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/shared/api/client";

import type { ChatMessage } from "./api";
import { useChatStore } from "./store";

const sendMessage = vi.hoisted(() =>
  vi.fn<(token: string, body: string) => Promise<ChatMessage>>(),
);
const fetchHistory = vi.hoisted(() => vi.fn());

vi.mock("./api", () => ({ sendMessage, fetchHistory }));

function message(position: number, body: string): ChatMessage {
  return {
    id: `m${position}`,
    position,
    author: { id: "a1", displayName: "lea.vale", role: "player" },
    body,
    sentAt: "2026-11-16T20:00:00Z",
    edited: false,
    deletedBy: null,
    roll: null,
  };
}

/** Le serveur accepte chaque envoi et lui donne la position suivante. */
function acceptEverything(): void {
  let position = 0;
  sendMessage.mockImplementation((_token, body) => {
    position += 1;
    return Promise.resolve(message(position, body));
  });
}

async function settle(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

beforeEach(() => {
  sendMessage.mockReset();
  fetchHistory.mockReset();
  useChatStore.getState().reset();
});

describe("useChatStore", () => {
  it("envoie à la suite deux messages saisis coup sur coup", async () => {
    acceptEverything();

    useChatStore.getState().send("premier");
    useChatStore.getState().send("second");
    await settle();

    const state = useChatStore.getState();
    expect(state.messages.map((m) => m.body)).toEqual(["premier", "second"]);
    expect(state.pending).toEqual([]);
  });

  it("garde le message en attente pendant une coupure et le renvoie avec le même jeton", async () => {
    sendMessage.mockRejectedValueOnce(new ApiError(0, "network_error"));
    useChatStore.getState().send("hors ligne");
    await settle();
    expect(useChatStore.getState().pending).toHaveLength(1);

    acceptEverything();
    await useChatStore.getState().flushPending();

    expect(useChatStore.getState().pending).toEqual([]);
    expect(sendMessage.mock.calls[0]?.[0]).toBe(sendMessage.mock.calls[1]?.[0]);
  });

  it("marque un envoi refusé sans bloquer les suivants", async () => {
    sendMessage.mockRejectedValueOnce(new ApiError(429, "rate_limited"));
    sendMessage.mockResolvedValueOnce(message(1, "second"));

    useChatStore.getState().send("premier");
    useChatStore.getState().send("second");
    await settle();

    const state = useChatStore.getState();
    expect(state.pending.map((p) => [p.body, p.errorCode])).toEqual([["premier", "rate_limited"]]);
    expect(state.messages.map((m) => m.body)).toEqual(["second"]);
  });

  it("remplace la version connue d'un message modifié ou supprimé", () => {
    useChatStore.getState().upsert(message(1, "avant"));
    useChatStore.getState().upsert({ ...message(1, "après"), edited: true });

    expect(useChatStore.getState().messages).toEqual([{ ...message(1, "après"), edited: true }]);
  });

  it("raccorde les messages récents à ceux déjà connus après une reconnexion", async () => {
    useChatStore.getState().upsert(message(1, "un"));
    fetchHistory.mockResolvedValue({
      messages: [message(1, "un"), message(2, "deux")],
      hasMore: false,
    });

    await useChatStore.getState().loadLatest();

    expect(useChatStore.getState().messages.map((m) => m.position)).toEqual([1, 2]);
  });
});
