/**
 * Proxy Next.js : pose une Content-Security-Policy stricte, avec un nonce
 * renouvelé à chaque requête. Les pages sont donc rendues dynamiquement.
 */
import { type NextRequest, NextResponse } from "next/server";

const isDevelopment = process.env.NODE_ENV === "development";

/** Adresse WebSocket du serveur temps réel, autorisée dans `connect-src`. */
const realtimeOrigin = process.env.NEXT_PUBLIC_REALTIME_URL ?? "";

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

export function proxy(request: NextRequest): NextResponse {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const contentSecurityPolicy = buildContentSecurityPolicy(nonce);

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", contentSecurityPolicy);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
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
