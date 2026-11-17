import { AuthScreen } from "@/features/auth/components/AuthScreen";
import { LoginForm } from "@/features/auth/components/LoginForm";
import type { SearchParams } from "@/features/auth/googleReturn";
import { requireGmBasePath } from "@/features/auth/requireGmBasePath";
import { labels } from "@/shared/i18n";

/** Connexion du MJ, servie par sa page secrète. */
export default async function GmLoginPage({
  searchParams,
}: {
  readonly searchParams: Promise<SearchParams>;
}) {
  const gmBasePath = requireGmBasePath();
  const params = await searchParams;

  return (
    <AuthScreen variant="gm" heading={labels.auth.gm.heading} subtitle={labels.auth.gm.subtitle}>
      <LoginForm portal="gm" gmBasePath={gmBasePath} searchParams={params} />
    </AuthScreen>
  );
}
