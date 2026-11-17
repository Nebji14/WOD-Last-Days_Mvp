import { AuthScreen } from "@/features/auth/components/AuthScreen";
import { LoginForm } from "@/features/auth/components/LoginForm";
import { requireGmBasePath } from "@/features/auth/requireGmBasePath";
import { labels } from "@/shared/i18n";

/** Connexion du MJ, servie par sa page secrète. */
export default function GmLoginPage() {
  const gmBasePath = requireGmBasePath();

  return (
    <AuthScreen variant="gm" heading={labels.auth.gm.heading} subtitle={labels.auth.gm.subtitle}>
      <LoginForm portal="gm" gmBasePath={gmBasePath} />
    </AuthScreen>
  );
}
