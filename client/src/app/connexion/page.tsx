import { AuthScreen } from "@/features/auth/components/AuthScreen";
import { LoginForm } from "@/features/auth/components/LoginForm";
import type { SearchParams } from "@/features/auth/googleReturn";
import { labels } from "@/shared/i18n";

/** Connexion des joueurs ; affiche aussi la notification après une déconnexion. */
export default async function PlayerLoginPage({
  searchParams,
}: {
  readonly searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  return (
    <AuthScreen
      variant="player"
      heading={labels.auth.login.heading}
      subtitle={labels.auth.login.subtitle}
    >
      <LoginForm portal="player" searchParams={params} />
    </AuthScreen>
  );
}
