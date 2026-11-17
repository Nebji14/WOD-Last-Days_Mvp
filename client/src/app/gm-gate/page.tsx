import { requireGmBasePath } from "@/features/auth/requireGmBasePath";
import { gmLoginPath } from "@/features/auth/routes";
import { TitleScreen } from "@/features/title/TitleScreen";

/** Écran titre ouvert depuis la page secrète du MJ : mène à la connexion du MJ. */
export default function GmTitlePage() {
  return <TitleScreen loginHref={gmLoginPath(requireGmBasePath())} />;
}
