import { requireGmBasePath } from "@/features/auth/requireGmBasePath";
import { gmLoginPath } from "@/features/auth/routes";
import { TitleScreen } from "@/features/title/TitleScreen";

/** Écran 01 ouvert depuis l'adresse dédiée du MJ : mène à la connexion du MJ (02c). */
export default function GmTitlePage() {
  return <TitleScreen loginHref={gmLoginPath(requireGmBasePath())} />;
}
