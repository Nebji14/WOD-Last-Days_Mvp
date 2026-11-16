/**
 * Client HTTP de l'API.
 *
 * Toutes les requêtes passent par le proxy `/api` du client (même origine) :
 * les cookies de session `HttpOnly` sont joints par le navigateur et ne sont
 * jamais lisibles par ce code.
 */

const REFRESH_PATH = "/api/auth/refresh";
const AUTH_PREFIX = "/api/auth/";
const SESSION_EXPIRED_CODE = "not_authenticated";

/** Précision jointe à une erreur : champ et règle en cause, ou donnée propre au code d'erreur. */
export type ApiErrorDetail = Readonly<Record<string, string>>;

/** Erreur renvoyée par l'API, ou panne réseau (`network_error`). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly details: readonly ApiErrorDetail[] = [],
    readonly requestId: string | null = null,
  ) {
    super(code);
    this.name = "ApiError";
  }
}

interface RequestOptions<T> {
  readonly method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  readonly body?: unknown;
  /** Valide et type le corps de la réponse. Omis pour une réponse sans corps. */
  readonly parse?: (data: unknown) => T;
}

let refreshInFlight: Promise<boolean> | null = null;

/**
 * Appelle l'API et retourne la réponse validée.
 *
 * Si la session a expiré, elle est renouvelée une fois puis la requête est
 * rejouée, sans intervention de l'utilisateur.
 *
 * @throws {ApiError} si l'API répond en erreur ou si le réseau est coupé.
 */
export async function apiRequest<T = void>(
  path: string,
  options: RequestOptions<T> = {},
): Promise<T> {
  let response = await send(path, options);

  if (await isExpiredSession(response, path)) {
    if (await refreshSession()) {
      response = await send(path, options);
    }
  }
  if (!response.ok) {
    throw await toApiError(response);
  }
  if (response.status === 204 || options.parse === undefined) {
    return undefined as T;
  }
  return options.parse(await response.json());
}

async function send<T>(path: string, options: RequestOptions<T>): Promise<Response> {
  try {
    return await fetch(path, {
      method: options.method ?? "GET",
      credentials: "same-origin",
      headers: options.body === undefined ? undefined : { "Content-Type": "application/json" },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch {
    throw new ApiError(0, "network_error");
  }
}

/** Les routes d'authentification gèrent elles-mêmes leurs erreurs 401. */
async function isExpiredSession(response: Response, path: string): Promise<boolean> {
  if (response.status !== 401 || path.startsWith(AUTH_PREFIX)) {
    return false;
  }
  const error = await toApiError(response.clone());
  return error.code === SESSION_EXPIRED_CODE;
}

/** Renouvelle la session. Les appels simultanés partagent la même tentative. */
function refreshSession(): Promise<boolean> {
  refreshInFlight ??= send(REFRESH_PATH, { method: "POST" })
    .then((response) => response.ok)
    .catch(() => false)
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

async function toApiError(response: Response): Promise<ApiError> {
  const body: unknown = await response.json().catch(() => null);
  const error = isRecord(body) && isRecord(body.error) ? body.error : {};
  return new ApiError(
    response.status,
    typeof error.code === "string" ? error.code : "internal_error",
    Array.isArray(error.details) ? error.details.filter(isRecord).map(toDetail) : [],
    typeof error.request_id === "string" ? error.request_id : null,
  );
}

/** Ne conserve que les propriétés textuelles d'une précision d'erreur. */
function toDetail(value: Record<string, unknown>): ApiErrorDetail {
  return Object.fromEntries(
    Object.entries(value).filter(
      (entry): entry is [string, string] => typeof entry[1] === "string",
    ),
  );
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
