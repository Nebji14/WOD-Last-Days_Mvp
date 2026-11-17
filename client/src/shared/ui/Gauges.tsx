/**
 * Jauges compactes d'un personnage : piste de santé et points de volonté.
 * Elles servent sur les sièges de la table et dans le profil ; la fiche a ses
 * propres jauges, plus grandes.
 */

const WOUND_STYLE: Record<string, string> = {
  "*": "border-copper bg-[#322218] text-copper-text",
  X: "border-copper-deep bg-[#251b15] text-copper",
  "/": "border-ink-muted bg-field text-ink",
};
const EMPTY_BOX = "border-line bg-panel";

interface HealthTrackProps {
  /** Nombre de cases : santé maximale effective. */
  readonly capacity: number;
  /** Blessures rangées par gravité : `*`, puis `X`, puis `/`. */
  readonly wounds: string;
  readonly label: string;
}

/** Taille des cases selon leur nombre, pour tenir sur la largeur d'un siège. */
function boxSize(capacity: number): string {
  if (capacity <= 9) {
    return "size-3 text-[10px]";
  }
  return capacity <= 14 ? "h-3 w-2 text-[8px]" : "h-3 w-1 text-[0px]";
}

export function HealthTrack({ capacity, wounds, label }: HealthTrackProps) {
  const boxes = Array.from({ length: capacity }, (_, index) => wounds[index] ?? "");
  return (
    <span
      role="img"
      aria-label={`${label} : ${wounds.length} / ${capacity}`}
      className={`flex ${capacity <= 9 ? "gap-1" : "gap-0.5"}`}
    >
      {boxes.map((wound, index) => (
        <span
          key={index}
          aria-hidden="true"
          className={`font-track flex items-center justify-center border leading-none font-bold ${boxSize(capacity)} ${
            WOUND_STYLE[wound] ?? EMPTY_BOX
          }`}
        >
          {wound}
        </span>
      ))}
    </span>
  );
}

interface WillpowerDotsProps {
  readonly max: number;
  readonly current: number;
  readonly label: string;
}

export function WillpowerDots({ max, current, label }: WillpowerDotsProps) {
  return (
    <span
      role="img"
      aria-label={`${label} : ${current} / ${max}`}
      className={`flex ${max <= 8 ? "gap-[5px]" : "gap-0.5"}`}
    >
      {Array.from({ length: max }, (_, index) => (
        <span
          key={index}
          aria-hidden="true"
          className={`rounded-full ${max <= 8 ? "size-[11px]" : "size-2"} ${
            index < current ? "bg-gold" : "border-line-strong border-[1.2px]"
          }`}
        />
      ))}
    </span>
  );
}
