/** Informations du compte et méthodes de connexion, en lecture. */
import type { Account, LoginMethods } from "@/features/auth/api";
import { labels } from "@/shared/i18n";

import { FormHeading } from "./AccountFormParts";

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

interface AccountSummaryProps {
  readonly account: Account;
  readonly methods: LoginMethods | null;
}

export function AccountSummary({ account, methods }: AccountSummaryProps) {
  const text = labels.profile;
  return (
    <>
      <div className="mt-6 mb-4">
        <FormHeading>{text.account.title}</FormHeading>
      </div>
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
      <div className="mt-7 mb-4">
        <FormHeading>{text.methods.title}</FormHeading>
      </div>
      <ul className="flex flex-col gap-2.5">
        <MethodRow label={text.methods.password} linked={methods?.password} />
        <MethodRow label={text.methods.google} linked={methods?.google} />
      </ul>
    </>
  );
}
