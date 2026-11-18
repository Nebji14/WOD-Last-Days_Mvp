/**
 * Case « Spécialité » d'un jet. Elle est toujours proposée : c'est le MJ qui
 * juge, à la table, si la spécialité s'applique.
 */
import { labels } from "@/shared/i18n";

interface SpecialtyOptionProps {
  readonly checked: boolean;
  readonly onChange: () => void;
  /** Texte d'aide affiché à côté du libellé ; masqué dans les panneaux étroits. */
  readonly compact?: boolean;
}

export function SpecialtyOption({ checked, onChange, compact = false }: SpecialtyOptionProps) {
  const text = labels.dice;
  return (
    <label className="text-ink flex items-center gap-2 text-base select-none">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span title={text.specialtyHint}>
        {text.specialty}
        {!compact && (
          <span className="text-ink-muted text-sm italic"> ({text.specialtyShort})</span>
        )}
      </span>
    </label>
  );
}
