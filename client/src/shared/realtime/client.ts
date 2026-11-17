/**
 * Client temps réel (WebSocket) de la table de jeu.
 *
 * La connexion s'ouvre avec un ticket à usage unique demandé à l'API : le
 * navigateur ne joint pas les cookies de session au serveur temps réel. Le
 * client ne fait que recevoir des événements ; toute action passe par l'API.
 *
 * En cas de coupure, la connexion est rouverte automatiquement, à intervalles
 * croissants.
 */
import { ApiError } from "@/shared/api/client";

/**
 * - `connecting` : première ouverture en cours ;
 * - `online` : événements reçus ;
 * - `reconnecting` : coupure, nouvelle tentative programmée ;
 * - `table_full` : les neuf places sont prises, aucune nouvelle tentative ;
 * - `unauthenticated` : session fermée ou expirée, aucune nouvelle tentative.
 */
export type RealtimeStatus =
  "connecting" | "online" | "reconnecting" | "table_full" | "unauthenticated";

export type RealtimeHandler = (data: unknown) => void;

export interface RealtimeClient {
  /** Ouvre la connexion et la maintient jusqu'à `stop`. */
  start(): void;
  /** Ferme la connexion et annule toute nouvelle tentative. */
  stop(): void;
  /** Abonne `handler` aux événements de ce type. Retourne la fonction de désabonnement. */
  on(type: string, handler: RealtimeHandler): () => void;
  /** Abonne `listener` aux changements d'état. Retourne la fonction de désabonnement. */
  onStatus(listener: (status: RealtimeStatus) => void): () => void;
}

interface RealtimeOptions {
  /** Adresse complète du point d'entrée WebSocket. */
  readonly url: string;
  /** Demande un ticket à l'API. Rejette avec une `ApiError` 401 si la session est fermée. */
  readonly fetchTicket: () => Promise<string>;
  /** Fabrique de WebSocket, remplaçable dans les tests. */
  readonly createSocket?: (url: string) => WebSocket;
}

const CLOSE_TABLE_FULL = 4409;
const RETRY_DELAYS_MS = [500, 1000, 2000, 4000, 8000] as const;

function isEvent(value: unknown): value is { type: string; data: unknown } {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { type?: unknown }).type === "string"
  );
}

export function createRealtimeClient(options: RealtimeOptions): RealtimeClient {
  const createSocket = options.createSocket ?? ((url: string) => new WebSocket(url));
  const handlers = new Map<string, Set<RealtimeHandler>>();
  const statusListeners = new Set<(status: RealtimeStatus) => void>();
  let socket: WebSocket | null = null;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  let attempts = 0;
  let running = false;
  // Incrémenté à chaque démarrage : une ouverture lancée avant un arrêt est ignorée.
  let generation = 0;
  let status: RealtimeStatus | null = null;

  function setStatus(next: RealtimeStatus): void {
    if (next === status) {
      return;
    }
    status = next;
    statusListeners.forEach((listener) => listener(next));
  }

  function scheduleRetry(): void {
    const delay = RETRY_DELAYS_MS[Math.min(attempts, RETRY_DELAYS_MS.length - 1)];
    attempts += 1;
    retryTimer = setTimeout(() => void open(generation), delay);
  }

  function dispatch(raw: unknown): void {
    if (typeof raw !== "string") {
      return;
    }
    let event: unknown;
    try {
      event = JSON.parse(raw);
    } catch {
      return;
    }
    if (!isEvent(event)) {
      return;
    }
    // Le premier événement confirme que le serveur a accepté le ticket.
    attempts = 0;
    setStatus("online");
    handlers.get(event.type)?.forEach((handler) => handler(event.data));
  }

  async function open(startedIn: number): Promise<void> {
    const isStale = (): boolean => !running || startedIn !== generation;
    retryTimer = null;
    let ticket: string;
    try {
      ticket = await options.fetchTicket();
    } catch (error) {
      if (isStale()) {
        return;
      }
      if (error instanceof ApiError && error.status === 401) {
        running = false;
        setStatus("unauthenticated");
      } else {
        setStatus("reconnecting");
        scheduleRetry();
      }
      return;
    }
    if (isStale()) {
      return;
    }
    const current = createSocket(options.url);
    socket = current;
    current.onopen = () => current.send(JSON.stringify({ type: "auth", ticket }));
    current.onmessage = (message) => dispatch(message.data);
    current.onclose = (event) => {
      if (socket !== current || !running) {
        return;
      }
      socket = null;
      if (event.code === CLOSE_TABLE_FULL) {
        running = false;
        setStatus("table_full");
        return;
      }
      setStatus("reconnecting");
      scheduleRetry();
    };
  }

  return {
    start() {
      if (running) {
        return;
      }
      running = true;
      generation += 1;
      attempts = 0;
      setStatus("connecting");
      void open(generation);
    },
    stop() {
      running = false;
      if (retryTimer !== null) {
        clearTimeout(retryTimer);
        retryTimer = null;
      }
      socket?.close();
      socket = null;
    },
    on(type, handler) {
      const set = handlers.get(type) ?? new Set<RealtimeHandler>();
      handlers.set(type, set);
      set.add(handler);
      return () => set.delete(handler);
    },
    onStatus(listener) {
      statusListeners.add(listener);
      return () => statusListeners.delete(listener);
    },
  };
}
