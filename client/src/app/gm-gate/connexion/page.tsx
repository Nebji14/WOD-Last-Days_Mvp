import { AuthScreen } from "@/features/auth/components/AuthScreen";
import { LoginForm } from "@/features/auth/components/LoginForm";
import { requireGmBasePath } from "@/features/auth/requireGmBasePath";
import { labels } from "@/shared/i18n";

/** Écran 02c — Connexion du MJ (adresse dédiée). */
export default function GmLoginPage() {
  const gmBasePath = requireGmBasePath();

  return (
    <AuthScreen variant="gm" heading={labels.auth.gm.heading} subtitle={labels.auth.gm.subtitle}>
      <LoginForm portal="gm" gmBasePath={gmBasePath} />
    </AuthScreen>
  );
}
