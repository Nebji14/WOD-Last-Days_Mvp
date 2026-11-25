/** Images d'un personnage sur sa carte du profil : une par forme. */
import { PortraitPicker } from "@/features/characters/components/PortraitPicker";
import type { Character } from "@/features/characters/model";
import type { PortraitFiles } from "@/features/characters/portrait";
import { labels } from "@/shared/i18n";

export interface PortraitActions {
  readonly onPortrait: (characterId: string, sheetId: string, files: PortraitFiles) => void;
  readonly onRemovePortrait: (characterId: string, sheetId: string) => void;
}

interface CharacterPortraitsProps extends PortraitActions {
  readonly character: Character;
  readonly busy: boolean;
}

export function CharacterPortraits(props: CharacterPortraitsProps) {
  const { character, busy, onPortrait, onRemovePortrait } = props;
  const text = labels.profile.characters;

  return (
    <ul aria-label={text.portraits} className="flex flex-wrap gap-x-6 gap-y-4 py-3">
      {character.sheets.map((sheet) => {
        const formName = sheet.is_main ? text.mainForm : sheet.form_name;
        return (
          <li key={sheet.id} className="flex w-52 flex-col items-center gap-1.5">
            <span className="text-ink-muted max-w-full truncate text-sm italic">{formName}</span>
            <PortraitPicker
              portrait={sheet.portrait}
              name={sheet.is_main ? (sheet.texts.name ?? "") : sheet.form_name}
              className="size-16 text-[19px]"
              busy={busy}
              onSave={(files) => onPortrait(character.id, sheet.id, files)}
              onRemove={() => onRemovePortrait(character.id, sheet.id)}
            />
          </li>
        );
      })}
    </ul>
  );
}
