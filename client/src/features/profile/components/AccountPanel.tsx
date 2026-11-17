/**
 * Panneau « Mon compte » du profil.
 *
 * Consultation seule : la modification du compte viendra après le MVP, le
 * bouton est donc grisé. Les méthodes de connexion sont listées avec leur
 * état, lu auprès du serveur.
 */
import type { Account } from "@/features/auth/api";
import { initials } from "@/features/table/seatLayout";
import { labels } from "@/shared/i18n";

import { useLoginMethods } from "../useLoginMethods";

const SECTION_TITLE = "font-display text-gold text-[11px] font-bold tracking-[3px]";
const ROW = "flex items-baseline justify-between gap-4 text-[17px]";

/** Ligne d'une méthode de connexion ; sans état tant qu'il n'est pas connu. */
function MethodRow({ label, linked }: { readonly label: string; readonly linked?: boolean }) {
  const text = labels.profile.methods;
  return (
    <li className={ROW}>
      <span className="text-ink">{label}</span>
      {linked === true && <span className="text-valid italic">✓ {text.enabled}</span>}
      {linked === false && <span className="text-ink-faint italic">{text.notLinked}</span>}
    </li>
  );
}

export function AccountPanel({ account }: { readonly account: Account }) {
  const text = labels.profile;
  const isGm = account.role === "gm";
  const methods = useLoginMethods();

  return (
    <section
      aria-label={text.account.title}
      className="border-line bg-panel flex flex-col rounded-xs border px-6 py-8"
    >
      <div className="flex flex-col items-center gap-2 border-line-soft border-b pb-6">
        <span
          aria-hidden="true"
          className="border-gold bg-field font-display text-gold flex size-28 items-center justify-center rounded-full border-2 text-5xl font-bold shadow-[0_0_24px_rgb(201_176_106/0.2)]"
        >
          {isGm ? labels.table.gm.initials : initials(account.displayName).slice(0, 1)}
        </span>
        <h2 className="text-ink-bright mt-3 text-3xl font-bold">{account.displayName}</h2>
        <p className="text-ink-muted flex items-center gap-2 italic">
          <span aria-hidden="true" className="bg-online size-2.5 rounded-full" />
          {isGm ? text.status.gm : text.status.player}
        </p>
      </div>

      <h3 className={`${SECTION_TITLE} mt-6 mb-4`}>{text.account.title}</h3>
      <dl className="flex flex-col gap-2.5">
        <div className={ROW}>
          <dt className="text-ink-muted">{text.account.displayName}</dt>
          <dd className="text-ink w-1/2 truncate">{account.displayName}</dd>
        </div>
        <div className={ROW}>
          <dt className="text-ink-muted">{text.account.username}</dt>
          <dd className="text-ink w-1/2 truncate">{account.username}</dd>
        </div>
        <div className={ROW}>
          <dt className="text-ink-muted">{text.account.state}</dt>
          <dd className="text-ink w-1/2">{text.account.active}</dd>
        </div>
      </dl>

      <h3 className={`${SECTION_TITLE} mt-7 mb-4`}>{text.methods.title}</h3>
      <ul className="flex flex-col gap-2.5">
        <MethodRow label={text.methods.password} linked={methods?.password} />
        <MethodRow label={text.methods.google} linked={methods?.google} />
      </ul>

      <button
        type="button"
        disabled
        className="border-line font-display text-ink-faint mt-auto h-10 cursor-not-allowed rounded-xs border text-[11px] font-bold tracking-[2.5px]"
      >
        {text.editInfo}
      </button>
      <p className="text-ink-faint mt-3 text-center text-[15px] italic">{text.editInfoLater}</p>
    </section>
  );
}
