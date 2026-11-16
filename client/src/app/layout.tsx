import type { Metadata } from "next";
import { Cinzel, Cormorant_Garamond, Inter, Limelight } from "next/font/google";
import { connection } from "next/server";
import type { ReactNode } from "react";

import { labels } from "@/shared/i18n";

import "./globals.css";

const cinzel = Cinzel({
  subsets: ["latin"],
  weight: ["700", "900"],
  variable: "--font-cinzel",
});
const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-cormorant",
});
const limelight = Limelight({ subsets: ["latin"], weight: "400", variable: "--font-limelight" });
const inter = Inter({ subsets: ["latin"], weight: ["400", "700"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: labels.app.title,
  description: labels.app.description,
  robots: { index: false, follow: false },
};

/**
 * Gabarit racine. Le rendu attend la requête (`connection`) : la politique de
 * sécurité du contenu repose sur un nonce propre à chaque requête (src/proxy.ts).
 */
export default async function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  await connection();
  const fontVariables = [cinzel, cormorant, limelight, inter]
    .map((font) => font.variable)
    .join(" ");

  return (
    <html lang="fr" className={fontVariables}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
