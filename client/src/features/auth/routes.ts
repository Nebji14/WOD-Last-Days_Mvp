/**
 * Adresses des écrans d'authentification.
 *
 * Le chemin du MJ est secret : il n'apparaît jamais dans une page joueur. Il est
 * mémorisé pour la session du navigateur une fois le MJ connecté, afin de le
 * ramener sur sa propre page de connexion après la déconnexion.
 */
export const PLAYER_LOGIN_PATH = "/connexion";
export const REGISTER_PATH = "/inscription";
export const TABLE_PATH = "/table";

const GM_BASE_STORAGE_KEY = "hunter:gm-base";

export function gmLoginPath(gmBasePath: string): string {
  return `${gmBasePath}/connexion`;
}

export function rememberGmBasePath(gmBasePath: string): void {
  window.sessionStorage.setItem(GM_BASE_STORAGE_KEY, gmBasePath);
}

/** Écran de connexion sur lequel revenir après une déconnexion, selon le rôle. */
export function loginPathAfterLogout(role: "player" | "gm"): string {
  const gmBasePath = window.sessionStorage.getItem(GM_BASE_STORAGE_KEY);
  return role === "gm" && gmBasePath ? gmLoginPath(gmBasePath) : PLAYER_LOGIN_PATH;
}
