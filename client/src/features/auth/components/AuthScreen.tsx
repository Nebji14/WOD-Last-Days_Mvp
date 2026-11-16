/**
 * Gabarit commun des écrans 02a, 02b, 02c et 08c : fond flouté, particules,
 * titre réduit et panneau central.
 *
 * La variante `gm` ajoute le bandeau « Accès maître du jeu » et la bordure
 * cuivre : on voit tout de suite que ce n'est pas la page joueur (02c).
 */
import type { ReactNode } from "react";

import { labels } from "@/shared/i18n";
import { EmberParticles } from "@/shared/ui/EmberParticles";
import { FlashToast } from "@/shared/ui/FlashToast";

interface AuthScreenProps {
  readonly variant: "player" | "gm";
  readonly heading: string;
  readonly subtitle: string;
  readonly children: ReactNode;
}

export function AuthScreen({ variant, heading, subtitle, children }: AuthScreenProps) {
  const isGm = variant === "gm";
  const panelFrame = isGm
    ? "border-copper-to shadow-[0_14px_40px_rgb(0_0_0/0.67),0_0_30px_rgb(183_119_77/0.2)]"
    : "border-line shadow-[0_14px_40px_rgb(0_0_0/0.6)]";

  return (
    <main className="bg-abyss relative flex min-h-screen flex-col items-center overflow-hidden pt-[52px] pb-10">
      <div
        aria-hidden="true"
        className="absolute -inset-2 bg-[url(/images/title-background.webp)] bg-cover bg-center blur-[5px]"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[radial-gradient(circle,rgb(5_2_2/0.25)_0%,rgb(5_2_2/0.7)_100%)]"
      />
      <EmberParticles className="opacity-70" />
      <FlashToast />

      <p className="font-display relative bg-[linear-gradient(180deg,#fff_0%,#fff6e8_60%,#ffc07a_100%)] bg-clip-text pl-[6px] text-[64px] leading-[86px] font-black tracking-[6px] text-transparent [filter:drop-shadow(0_0_18px_rgb(255_90_20/0.8))]">
        {labels.app.game}
      </p>

      {isGm && (
        <p className="border-copper text-copper-light font-display relative mt-2 flex h-[22px] items-center rounded-full border bg-[#322218] px-3.5 text-[9px] font-bold tracking-[2.5px]">
          {labels.auth.gm.banner}
        </p>
      )}

      <section
        className={`relative flex w-[440px] flex-col gap-[18px] border bg-[rgb(17_14_12/0.88)] px-10 py-[34px] backdrop-blur-[6px] ${panelFrame} ${
          isGm ? "mt-[7px]" : "mt-[37px]"
        }`}
      >
        <div
          aria-hidden="true"
          className="border-line-soft pointer-events-none absolute inset-1 border"
        />

        <div className="flex items-center gap-3.5">
          <HeadingRule />
          <h1 className="font-poster text-ink text-[30px] leading-[37px] whitespace-nowrap">
            {heading}
          </h1>
          <HeadingRule />
        </div>
        <p className="text-ink-muted text-center text-lg leading-[22px] font-medium italic">
          {subtitle}
        </p>

        {children}
      </section>
    </main>
  );
}

/** Double filet de part et d'autre du titre du panneau. */
function HeadingRule() {
  return <span aria-hidden="true" className="border-line block h-[5px] flex-1 border-y" />;
}
