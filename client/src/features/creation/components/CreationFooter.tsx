"use client";

/**
 * Pied de l'assistant : « Précédent », raison du blocage éventuel et
 * « Suivant », actif seulement quand l'étape est valide. À la dernière étape,
 * « Suivant » devient « Créer le personnage ».
 */
import { labels } from "@/shared/i18n";

const BUTTON =
  "font-display flex h-11 w-[190px] items-center justify-center gap-3 rounded-xs border text-[12px] font-bold tracking-[3px]";

interface CreationFooterProps {
  /** Raison du blocage ou erreur de création ; `null` si rien à signaler. */
  readonly message: string | null;
  readonly canGoBack: boolean;
  readonly canGoOn: boolean;
  readonly last: boolean;
  readonly busy: boolean;
  readonly onBack: () => void;
  readonly onNext: () => void;
}

export function CreationFooter(props: CreationFooterProps) {
  const { message, canGoBack, canGoOn, last, busy, onBack, onNext } = props;
  const text = labels.creation;

  return (
    <footer className="flex h-[84px] shrink-0 items-center justify-between gap-6 px-8">
      <button
        type="button"
        onClick={onBack}
        disabled={!canGoBack}
        className={`${BUTTON} border-line-strong text-ink cursor-pointer hover:brightness-125 disabled:invisible`}
      >
        <span aria-hidden="true">←</span>
        {text.previous}
      </button>
      <p role="status" className="text-danger flex-1 text-center text-[15px] italic">
        {busy ? text.creating : message}
      </p>
      <button
        type="button"
        onClick={onNext}
        disabled={!canGoOn}
        className={`${BUTTON} ${last ? "w-[240px]" : ""} from-blood-from to-blood-to border-blood-line text-ink-bright cursor-pointer bg-linear-to-b shadow-[0_0_12px_rgb(216_53_44/0.3)] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-35 disabled:shadow-none`}
      >
        {last ? text.create : text.next}
        {!last && <span aria-hidden="true">→</span>}
      </button>
    </footer>
  );
}
