/**
 * Message « mauvaise page » : des identifiants valides ont
 * été saisis sur l'accès de l'autre rôle. Aucune session n'est ouverte.
 */
import Link from "next/link";

import { labels } from "@/shared/i18n";

interface WrongPortalMessageProps {
  /** Rôle du compte saisi : `gm` sur la page des joueurs, `player` sur celle du MJ. */
  readonly accountRole: "gm" | "player";
  /** Écran de connexion du bon accès ; `null` si le serveur ne l'a pas communiqué. */
  readonly href: string | null;
}

export function WrongPortalMessage({ accountRole, href }: WrongPortalMessageProps) {
  const isGm = accountRole === "gm";
  const text = labels.auth.wrongPortal;

  return (
    <div
      role="alert"
      className="border-blood-line bg-danger-panel flex flex-col gap-1.5 rounded-md border px-5 py-4 shadow-[0_0_20px_rgb(216_53_44/0.25)]"
    >
      <p className="font-display text-danger-bright text-sm font-bold tracking-[3px]">
        {isGm ? text.gmTitle : text.playerTitle}
      </p>
      <p className="text-ink-bright text-lg leading-[1.3] font-semibold italic">
        {isGm ? labels.errors.wrong_portal_gm : labels.errors.wrong_portal_player}
      </p>
      {href !== null && (
        <Link href={href} className="text-gold text-base font-bold whitespace-pre underline">
          {isGm ? text.gmLink : text.playerLink}
        </Link>
      )}
    </div>
  );
}
