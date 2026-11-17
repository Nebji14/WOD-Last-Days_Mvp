"use client";

/**
 * Écran titre, commun aux joueurs et au MJ : seule la destination change selon
 * l'adresse utilisée.
 *
 * La scène garde ses proportions (1440 × 900) : positions en pourcentage et
 * tailles en unités de conteneur (`cqw`).
 */
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { labels } from "@/shared/i18n";
import { EmberParticles } from "@/shared/ui/EmberParticles";

interface TitleScreenProps {
  /** Page de connexion de l'adresse utilisée : celle des joueurs ou celle du MJ. */
  readonly loginHref: string;
}

const TITLE_GRADIENT =
  "bg-[linear-gradient(180deg,#fff_0%,#fff6e8_55%,#ffe2b8_85%,#ffc07a_100%)] bg-[length:100%_135%] bg-clip-text text-transparent";
const TITLE_SHADOWS =
  "[filter:drop-shadow(0_0_1.6cqw_rgb(255_90_20/0.8))_drop-shadow(0_-0.5cqw_3.2cqw_rgb(255_138_42/0.4))_drop-shadow(0_0.7cqw_1.5cqw_rgb(0_0_0/0.7))]";

export function TitleScreen({ loginHref }: TitleScreenProps) {
  const router = useRouter();
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setLeaving(true);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <main className="bg-abyss relative h-screen overflow-hidden">
      <div
        aria-hidden="true"
        className="animate-title-bg absolute inset-0 bg-[url(/images/title-background.webp)] bg-cover bg-center"
      />
      <EmberParticles className="animate-title-bg" />

      <div className="@container absolute top-1/2 left-1/2 aspect-[16/10] w-[min(100vw,160vh)] -translate-x-1/2 -translate-y-1/2">
        <div
          aria-hidden="true"
          className="animate-title-halo absolute top-[25.5%] left-[18.75%] h-[42.2%] w-[62.5%] rounded-full bg-[radial-gradient(closest-side,rgb(255_106_26/0.4)_0%,rgb(151_86_43/0.2)_45%,transparent_100%)] blur-[2.8cqw]"
        />

        <h1 className="animate-title-smoke font-display absolute inset-x-0 top-[27.8%] text-center text-[14.58cqw] leading-[1.35] font-black tracking-[0.0857em]">
          <span aria-hidden="true" className="text-ember absolute inset-0 opacity-75 blur-[1.9cqw]">
            {labels.app.game}
          </span>
          <span className={`relative inline-block ${TITLE_SHADOWS}`}>
            <span className={`animate-flame-shift inline-block pl-[0.0857em] ${TITLE_GRADIENT}`}>
              {labels.app.game}
            </span>
          </span>
        </h1>

        <p className="animate-title-sub font-display text-title-sub absolute inset-x-0 top-[57.8%] pl-[1.94cqw] text-center text-[3.19cqw] leading-[1.35] font-bold tracking-[1.94cqw] [text-shadow:0_0_1.25cqw_rgb(255_90_20/0.8)]">
          {labels.app.campaign}
        </p>

        <div
          aria-hidden="true"
          className="absolute top-[63.3%] left-[22.2%] h-[10.2%] w-[55.6%] rounded-full bg-[radial-gradient(closest-side,rgb(5_2_2/0.85)_0%,rgb(5_2_2/0.5)_60%,transparent_100%)] blur-[0.8cqw]"
        />

        <div className="animate-title-prompt absolute inset-x-0 top-[73.3%] flex justify-center">
          <button
            type="button"
            onClick={() => setLeaving(true)}
            className={`text-ink flex cursor-pointer items-center gap-[1.5cqw] text-[1.8cqw] font-semibold tracking-[0.62cqw] [text-shadow:0_0_1cqw_rgb(255_106_26/0.8)] ${
              leaving ? "animate-prompt-confirm" : "animate-prompt-blink"
            }`}
          >
            <Rule />
            <span className="pl-[0.62cqw]">{labels.title.prompt}</span>
            <Rule />
          </button>
        </div>
      </div>

      {leaving && (
        <div
          aria-hidden="true"
          className="animate-fade-to-black absolute inset-0 bg-black [animation-delay:0.6s]"
          onAnimationEnd={() => router.push(loginHref)}
        />
      )}
    </main>
  );
}

/** Double filet doré qui encadre l'invite. */
function Rule() {
  return (
    <span aria-hidden="true" className="border-gold/70 block h-[0.35cqw] w-[6.25cqw] border-y" />
  );
}
