import Link from "next/link";

import { labels } from "@/shared/i18n";

/** Page 404. Elle sert aussi de réponse à tout chemin d'accès MJ inconnu. */
export default function NotFound() {
  return (
    <main className="bg-abyss flex min-h-screen flex-col items-center justify-center gap-5">
      <p className="font-display text-ink text-2xl font-bold tracking-[0.3em]">
        {labels.notFound.title}
      </p>
      <Link href="/" className="text-gold text-lg font-semibold underline">
        {labels.notFound.back}
      </Link>
    </main>
  );
}
