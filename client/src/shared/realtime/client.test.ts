import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/shared/api/client";

import { createRealtimeClient, type RealtimeStatus } from "./client";

/** WebSocket minimal piloté par le test. */
class FakeSocket {
  static readonly opened: FakeSocket[] = [];
  readonly sent: string[] = [];
  closed = false;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: unknown }) => void) | null = null;
  onclose: ((event: { code: number }) => void) | null = null;

  constructor(readonly url: string) {
    FakeSocket.opened.push(this);
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.closed = true;
  }

  serverSends(type: string, data: unknown): void {
    this.onmessage?.({ data: JSON.stringify({ type, data }) });
  }

  serverCloses(code: number): void {
    this.onclose?.({ code });
  }
}

function setup(fetchTicket: () => Promise<string> = () => Promise.resolve("ticket-1")) {
  const statuses: RealtimeStatus[] = [];
  const client = createRealtimeClient({
    url: "ws://serveur/ws",
    fetchTicket,
    createSocket: (url) => new FakeSocket(url) as unknown as WebSocket,
  });
  client.onStatus((status) => statuses.push(status));
  return { client, statuses };
}

/** Laisse s'exécuter les promesses en attente (demande de ticket). */
async function settle(): Promise<void> {
  await vi.advanceTimersByTimeAsync(0);
}

beforeEach(() => {
  vi.useFakeTimers();
  FakeSocket.opened.length = 0;
});

afterEach(() => {
  vi.useRealTimers();
});

describe("createRealtimeClient", () => {
  it("présente le ticket à l'ouverture puis passe en ligne au premier événement", async () => {
    const { client, statuses } = setup();
    const received: unknown[] = [];
    client.on("table.state", (data) => received.push(data));

    client.start();
    await settle();
    const socket = FakeSocket.opened[0];
    socket?.onopen?.();
    socket?.serverSends("table.state", { seats: [] });

    expect(socket?.url).toBe("ws://serveur/ws");
    expect(socket?.sent).toEqual([JSON.stringify({ type: "auth", ticket: "ticket-1" })]);
    expect(received).toEqual([{ seats: [] }]);
    expect(statuses).toEqual(["connecting", "online"]);
  });

  it("ne transmet un événement qu'aux abonnés de son type, jusqu'au désabonnement", async () => {
    const { client } = setup();
    const chat = vi.fn();
    const unsubscribe = client.on("chat.message", chat);
    client.start();
    await settle();
    const socket = FakeSocket.opened[0];

    socket?.serverSends("table.state", {});
    socket?.serverSends("chat.message", { id: "m1" });
    unsubscribe();
    socket?.serverSends("chat.message", { id: "m2" });

    expect(chat).toHaveBeenCalledTimes(1);
    expect(chat).toHaveBeenCalledWith({ id: "m1" });
  });

  it("ignore les messages qui ne sont pas des événements", async () => {
    const { client, statuses } = setup();
    client.start();
    await settle();

    FakeSocket.opened[0]?.onmessage?.({ data: "pas du json" });
    FakeSocket.opened[0]?.onmessage?.({ data: JSON.stringify([1, 2]) });

    expect(statuses).toEqual(["connecting"]);
  });

  it("rouvre la connexion avec un nouveau ticket après une coupure", async () => {
    const fetchTicket = vi
      .fn<() => Promise<string>>()
      .mockResolvedValueOnce("ticket-1")
      .mockResolvedValueOnce("ticket-2");
    const { client, statuses } = setup(fetchTicket);
    client.start();
    await settle();
    FakeSocket.opened[0]?.serverSends("table.state", {});

    FakeSocket.opened[0]?.serverCloses(1006);
    await vi.advanceTimersByTimeAsync(500);
    FakeSocket.opened[1]?.onopen?.();
    FakeSocket.opened[1]?.serverSends("table.state", {});

    expect(FakeSocket.opened[1]?.sent).toEqual([
      JSON.stringify({ type: "auth", ticket: "ticket-2" }),
    ]);
    expect(statuses).toEqual(["connecting", "online", "reconnecting", "online"]);
  });

  it("retente quand le serveur est injoignable au moment de demander le ticket", async () => {
    const fetchTicket = vi
      .fn<() => Promise<string>>()
      .mockRejectedValueOnce(new ApiError(0, "network_error"))
      .mockResolvedValueOnce("ticket-2");
    const { client, statuses } = setup(fetchTicket);

    client.start();
    await settle();
    await vi.advanceTimersByTimeAsync(500);

    expect(FakeSocket.opened).toHaveLength(1);
    expect(statuses).toEqual(["connecting", "reconnecting"]);
  });

  it("s'arrête quand la session est fermée", async () => {
    const fetchTicket = vi
      .fn<() => Promise<string>>()
      .mockRejectedValue(new ApiError(401, "not_authenticated"));
    const { client, statuses } = setup(fetchTicket);

    client.start();
    await settle();
    await vi.advanceTimersByTimeAsync(60_000);

    expect(fetchTicket).toHaveBeenCalledTimes(1);
    expect(FakeSocket.opened).toHaveLength(0);
    expect(statuses).toEqual(["connecting", "unauthenticated"]);
  });

  it("ne retente pas quand la table est complète", async () => {
    const { client, statuses } = setup();
    client.start();
    await settle();

    FakeSocket.opened[0]?.serverCloses(4409);
    await vi.advanceTimersByTimeAsync(60_000);

    expect(FakeSocket.opened).toHaveLength(1);
    expect(statuses).toEqual(["connecting", "table_full"]);
  });

  it("ferme la connexion et n'en rouvre aucune après stop", async () => {
    const { client } = setup();
    client.start();
    await settle();

    client.stop();
    FakeSocket.opened[0]?.serverCloses(1000);
    await vi.advanceTimersByTimeAsync(60_000);

    expect(FakeSocket.opened[0]?.closed).toBe(true);
    expect(FakeSocket.opened).toHaveLength(1);
  });

  it("n'ouvre qu'une connexion après un arrêt suivi d'un redémarrage immédiat", async () => {
    const { client } = setup();

    client.start();
    client.stop();
    client.start();
    await settle();

    expect(FakeSocket.opened).toHaveLength(1);
  });
});
