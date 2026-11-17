import { PLAYER_LOGIN_PATH } from "@/features/auth/routes";
import { TitleScreen } from "@/features/title/TitleScreen";

/** Écran titre des joueurs : mène à la connexion des joueurs. */
export default function PlayerTitlePage() {
  return <TitleScreen loginHref={PLAYER_LOGIN_PATH} />;
}
