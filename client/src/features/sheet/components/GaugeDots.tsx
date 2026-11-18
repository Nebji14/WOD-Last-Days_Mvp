/**
 * Points disponibles d'une jauge (Volonté, ressource libre) : un point plein par
 * point disponible, cliquables à tout moment pour dépenser ou récupérer.
 * Cliquer le dernier point plein le vide.
 */
interface GaugeDotsProps {
  /** Nom de la jauge, repris par les lecteurs d'écran. */
  readonly label: string;
  /** Texte « 3 disponibles sur 5 ». */
  readonly summary: string;
  readonly current: number;
  readonly max: number;
  readonly onChange: (value: number) => void;
}

export function GaugeDots({ label, summary, current, max, onChange }: GaugeDotsProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span role="group" aria-label={summary} className="flex flex-wrap gap-1.5">
        {Array.from({ length: max }, (_, index) => index + 1).map((rank) => (
          <button
            key={rank}
            type="button"
            aria-label={`${label} ${rank}`}
            onClick={() => onChange(rank === current ? rank - 1 : rank)}
            className={`size-[18px] cursor-pointer rounded-full hover:brightness-150 ${
              rank <= current ? "bg-gold" : "border-gold/70 border-[1.5px]"
            }`}
          />
        ))}
      </span>
      <span className="text-ink shrink-0 text-base font-semibold">{summary}</span>
    </div>
  );
}
