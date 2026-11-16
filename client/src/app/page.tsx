import { PLAYER_LOGIN_PATH } from "@/features/auth/routes";
import { TitleScreen } from "@/features/title/TitleScreen";

/** Écran 01 ouvert depuis l'adresse des joueurs : mène à la connexion joueur (02a). */
export default function PlayerTitlePage() {
  return <TitleScreen loginHref={PLAYER_LOGIN_PATH} />;
}
