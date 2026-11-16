/**
 * Proxy Next.js.
 *
 * 1. Pose une Content-Security-Policy stricte, avec un nonce renouvelé à chaque
 *    requête. Les pages sont donc rendues dynamiquement.
 * 2. Sert l'accès dédié du MJ (US-023, décision T-4) : le chemin réservé est
 *    réécrit vers le segment interne, et ce segment répond 404 s'il est demandé
 *    directement.
 */
import { type NextRequest, NextResponse } from "next/server";

import { configuredGmAccessPath, INTERNAL_GM_SEGMENT } from "@/features/auth/gmAccess";

const isDevelopment = process.env.NODE_ENV === "development";

/** Adresse WebSocket du serveur temps réel, autorisée dans `connect-src`. */
const realtimeOrigin = process.env.NEXT_PUBLIC_REALTIME_URL ?? "";

/** Chemin sans page associée : la réécriture vers lui produit la page 404 standard. */
const NOT_FOUND_PATH = "/_introuvable";

/**
 * Construit la politique de sécurité du contenu.
 *
 * `unsafe-eval` et `unsafe-inline` ne sont accordés qu'en développement, où
 * React et le rechargement à chaud en ont besoin.
 */
function buildContentSecurityPolicy(nonce: string): string {
  const directives = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDevelopment ? " 'unsafe-eval'" : ""}`,
    isDevelopment ? "style-src 'self' 'unsafe-inline'" : `style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' blob: data: https://*.supabase.co",
    "font-src 'self'",
    `connect-src 'self' ${realtimeOrigin}`.trim(),
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ];
  if (!isDevelopment) {
    directives.push("upgrade-insecure-requests");
  }
  return directives.join("; ");
}

/** Indique si `pathname` est `base` ou l'un de ses sous-chemins. */
function isUnder(pathname: string, base: string): boolean {
  return pathname === base || pathname.startsWith(`${base}/`);
}

/**
 * Retourne le chemin interne à servir à la place de `pathname`, ou `null` si la
 * requête ne concerne pas l'accès du MJ.
 */
function resolveGmRewrite(pathname: string): string | null {
  const internalBase = `/${INTERNAL_GM_SEGMENT}`;
  if (isUnder(pathname, internalBase)) {
    return NOT_FOUND_PATH;
  }
  const gmAccessPath = configuredGmAccessPath();
  if (gmAccessPath !== null && isUnder(pathname, `/${gmAccessPath}`)) {
    return internalBase + pathname.slice(gmAccessPath.length + 1);
  }
  return null;
}

export function proxy(request: NextRequest): NextResponse {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const contentSecurityPolicy = buildContentSecurityPolicy(nonce);

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", contentSecurityPolicy);

  const rewritePath = resolveGmRewrite(request.nextUrl.pathname);
  const forwarded = { request: { headers: requestHeaders } };
  const response =
    rewritePath === null
      ? NextResponse.next(forwarded)
      : NextResponse.rewrite(new URL(rewritePath, request.url), forwarded);

  response.headers.set("Content-Security-Policy", contentSecurityPolicy);
  return response;
}

export const config = {
  matcher: [
    {
      source: "/((?!api|_next/static|_next/image|images|favicon.ico).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
