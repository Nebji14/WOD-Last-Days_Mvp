/** Éléments partagés par les formulaires de connexion et d'inscription. */
import Link from "next/link";

import { labels } from "@/shared/i18n";

/** Message d'erreur affiché sous les champs. */
export function FormError({ message }: { readonly message: string }) {
  return (
    <p role="alert" className="text-danger text-[17px] leading-snug font-semibold">
      {message}
    </p>
  );
}

/** Séparateur « ou » entre l'action principale et la connexion Google. */
export function OrSeparator() {
  return (
    <div className="flex items-center gap-3">
      <span aria-hidden="true" className="bg-line h-px flex-1" />
      <span className="text-ink-muted text-[17px] leading-[21px] font-medium italic">
        {labels.auth.or}
      </span>
      <span aria-hidden="true" className="bg-line h-px flex-1" />
    </div>
  );
}

/**
 * Bouton de connexion Google.
 *
 * Désactivé tant que le fournisseur Google n'est pas branché.
 */
export function GoogleButton({ label }: { readonly label: string }) {
  return (
    <button
      type="button"
      disabled
      title={labels.auth.googleSoon}
      className="border-line bg-panel text-ink flex h-12 w-full items-center justify-center gap-3 rounded-xs border text-[19px] font-semibold disabled:cursor-not-allowed disabled:opacity-50"
    >
      <span
        aria-hidden="true"
        className="bg-ink font-display flex size-6 items-center justify-center rounded-full text-sm font-bold text-[#120e0c]"
      >
        G
      </span>
      {label}
    </button>
  );
}

interface FooterLinkProps {
  readonly prompt: string;
  readonly label: string;
  readonly href: string;
}

/** Ligne de bas de panneau : question suivie d'un lien vers l'autre écran. */
export function FooterLink({ prompt, label, href }: FooterLinkProps) {
  return (
    <p className="text-ink-muted pt-1.5 text-center text-[17px] leading-[21px] font-medium">
      {prompt}{" "}
      <Link href={href} className="text-gold font-bold underline">
        {label}
      </Link>
    </p>
  );
}
