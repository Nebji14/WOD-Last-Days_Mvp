import { AuthScreen } from "@/features/auth/components/AuthScreen";
import { LoginForm } from "@/features/auth/components/LoginForm";
import { labels } from "@/shared/i18n";

/** Connexion des joueurs ; affiche aussi la notification après une déconnexion. */
export default function PlayerLoginPage() {
  return (
    <AuthScreen
      variant="player"
      heading={labels.auth.login.heading}
      subtitle={labels.auth.login.subtitle}
    >
      <LoginForm portal="player" />
    </AuthScreen>
  );
}
