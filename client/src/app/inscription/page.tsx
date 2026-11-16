import { AuthScreen } from "@/features/auth/components/AuthScreen";
import { RegisterForm } from "@/features/auth/components/RegisterForm";
import { labels } from "@/shared/i18n";

/** Écran 02b — Inscription (joueur). */
export default function RegisterPage() {
  return (
    <AuthScreen
      variant="player"
      heading={labels.auth.register.heading}
      subtitle={labels.auth.register.subtitle}
    >
      <RegisterForm />
    </AuthScreen>
  );
}
