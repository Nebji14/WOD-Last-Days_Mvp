import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiRequest } from "./client";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status });
}

function apiErrorBody(code: string, details?: unknown[]): unknown {
  return { error: { code, message: "…", request_id: "req-1", details } };
}

function mockFetch(...responses: Response[]) {
  const fetchMock = vi.fn<typeof fetch>();
  responses.forEach((response) => fetchMock.mockResolvedValueOnce(response));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("retourne la réponse validée par le parseur", async () => {
    mockFetch(jsonResponse(200, { value: 3 }));

    const result = await apiRequest("/api/x", {
      parse: (data) => (data as { value: number }).value,
    });

    expect(result).toBe(3);
  });

  it("envoie le corps en JSON avec les cookies de même origine", async () => {
    const fetchMock = mockFetch(new Response(null, { status: 204 }));

    await apiRequest("/api/x", { method: "POST", body: { a: 1 } });

    expect(fetchMock).toHaveBeenCalledWith("/api/x", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: '{"a":1}',
    });
  });

  it("convertit une erreur de l'API en ApiError avec code, détails et identifiant", async () => {
    mockFetch(jsonResponse(422, apiErrorBody("password_too_weak", [{ rule: "digit" }])));

    const error = await apiRequest("/api/auth/register", { method: "POST" }).catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 422,
      code: "password_too_weak",
      details: [{ rule: "digit" }],
      requestId: "req-1",
    });
  });

  it("signale une coupure réseau par le code network_error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(apiRequest("/api/x")).rejects.toMatchObject({ code: "network_error", status: 0 });
  });

  it("renouvelle la session expirée puis rejoue la requête", async () => {
    const fetchMock = mockFetch(
      jsonResponse(401, apiErrorBody("not_authenticated")),
      new Response(null, { status: 204 }),
      jsonResponse(200, { ok: true }),
    );

    const result = await apiRequest("/api/table", { parse: (data) => data });

    expect(result).toEqual({ ok: true });
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      "/api/table",
      "/api/auth/refresh",
      "/api/table",
    ]);
  });

  it("abandonne si le renouvellement de session échoue", async () => {
    mockFetch(
      jsonResponse(401, apiErrorBody("not_authenticated")),
      jsonResponse(401, apiErrorBody("not_authenticated")),
    );

    await expect(apiRequest("/api/table")).rejects.toMatchObject({ status: 401 });
  });

  it("ne tente aucun renouvellement sur les routes d'authentification", async () => {
    const fetchMock = mockFetch(jsonResponse(401, apiErrorBody("invalid_credentials")));

    await expect(apiRequest("/api/auth/login", { method: "POST" })).rejects.toMatchObject({
      code: "invalid_credentials",
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
