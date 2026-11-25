/**
 * Chargement du lecteur intégré officiel de YouTube.
 *
 * Seules les fonctions utilisées sont décrites. Le script n'est chargé qu'une
 * fois, quand un participant active le son.
 */

export interface YouTubePlayer {
  loadVideoById(options: { videoId: string; startSeconds: number }): void;
  cueVideoById(options: { videoId: string; startSeconds: number }): void;
  playVideo(): void;
  pauseVideo(): void;
  seekTo(seconds: number, allowSeekAhead: boolean): void;
  setVolume(volume: number): void;
  unMute(): void;
  getCurrentTime(): number;
  getPlayerState(): number;
  destroy(): void;
}

interface PlayerOptions {
  readonly host: string;
  readonly videoId: string;
  readonly width: string;
  readonly height: string;
  readonly playerVars: Readonly<Record<string, string | number>>;
  readonly events: {
    readonly onReady: () => void;
    readonly onError: (event: { readonly data: number }) => void;
  };
}

interface YouTubeApi {
  readonly Player: new (element: HTMLElement, options: PlayerOptions) => YouTubePlayer;
}

declare global {
  interface Window {
    YT?: YouTubeApi;
    onYouTubeIframeAPIReady?: () => void;
  }
}

/** États du lecteur utiles à la synchronisation. */
export const PLAYER_UNSTARTED = -1;
export const PLAYER_PLAYING = 1;
export const PLAYER_CUED = 5;

/** Vidéo retirée ou interdite d'intégration : elle ne se jouera chez personne. */
const UNPLAYABLE_ERRORS: ReadonlySet<number> = new Set([100, 101, 150]);

const API_URL = "https://www.youtube.com/iframe_api";
/** Mode confidentialité du lecteur : pas de suivi ni de publicité personnalisée. */
const PRIVACY_HOST = "https://www.youtube-nocookie.com";

let apiInFlight: Promise<YouTubeApi> | null = null;

function loadApi(): Promise<YouTubeApi> {
  apiInFlight ??= new Promise<YouTubeApi>((resolve, reject) => {
    if (window.YT?.Player) {
      resolve(window.YT);
      return;
    }
    const script = document.createElement("script");
    const fail = (): void => {
      script.remove();
      apiInFlight = null;
      reject(new Error("Lecteur de musique injoignable"));
    };
    window.onYouTubeIframeAPIReady = () => (window.YT ? resolve(window.YT) : fail());
    script.src = API_URL;
    script.async = true;
    script.onerror = fail;
    document.head.append(script);
  });
  return apiInFlight;
}

interface PlayerHandlers {
  readonly onReady: (player: YouTubePlayer) => void;
  /** Le morceau ne se joue chez personne. */
  readonly onUnplayable: () => void;
  /** Le lecteur lui-même est en échec, sur cet écran seulement. */
  readonly onFailure: () => void;
}

/**
 * Monte un lecteur dans `container`.
 *
 * @param videoId vidéo affichée à l'ouverture, sans lecture.
 * @returns la fonction qui le démonte.
 */
export function mountPlayer(
  container: HTMLElement,
  videoId: string,
  handlers: PlayerHandlers,
): () => void {
  let disposed = false;
  let player: YouTubePlayer | null = null;
  // L'API remplace cet élément par son cadre : React ne doit pas en être propriétaire.
  const target = document.createElement("div");
  container.append(target);

  loadApi()
    .then((api) => {
      if (disposed) {
        return;
      }
      const created = new api.Player(target, {
        host: PRIVACY_HOST,
        videoId,
        width: "100%",
        height: "100%",
        playerVars: {
          controls: 0,
          disablekb: 1,
          fs: 0,
          iv_load_policy: 3,
          playsinline: 1,
          rel: 0,
          origin: window.location.origin,
        },
        events: {
          onReady: () => !disposed && handlers.onReady(created),
          onError: ({ data }) => {
            if (disposed) {
              return;
            }
            if (UNPLAYABLE_ERRORS.has(data)) {
              handlers.onUnplayable();
            } else {
              handlers.onFailure();
            }
          },
        },
      });
      player = created;
    })
    .catch(() => !disposed && handlers.onFailure());

  return () => {
    disposed = true;
    player?.destroy();
    container.replaceChildren();
  };
}
