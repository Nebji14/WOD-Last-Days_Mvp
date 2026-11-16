import { labels } from "@/shared/i18n";

/** Page d'accueil provisoire : l'écran titre (01) la remplace à l'étape 2. */
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6">
      <h1 className="font-display text-7xl font-black tracking-[0.08em] text-white">
        {labels.app.game}
      </h1>
      <p className="font-display text-title-sub text-2xl font-bold tracking-[0.6em]">
        {labels.app.campaign}
      </p>
    </main>
  );
}
