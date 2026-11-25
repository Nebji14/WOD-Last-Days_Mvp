"use client";

/**
 * Panneau « Identité » : portrait de la forme, nom, joueur, concept, profession, vertu, vice,
 * compact. Pour un PNJ, la ligne du joueur devient la catégorie.
 */
import { setSheetField } from "@/features/characters/api";
import { labels } from "@/shared/i18n";

import { NpcCategoryLine } from "./NpcPanels";
import { PANEL, SMALL_LABEL, TextValue, useSheet } from "./primitives";
import { SheetPortrait } from "./SheetPortrait";

const FIELDS = ["concept", "profession", "virtue", "vice", "compact"] as const;

export function IdentityPanel() {
  const { character, sheet, editing, run } = useSheet();
  const text = labels.sheet;
  const save = (field: string) => (value: string) =>
    void run(() => setSheetField(sheet.id, field, value, sheet.texts[field] ?? ""));

  return (
    <section className={`${PANEL} flex min-h-[104px] items-center gap-6 px-6 py-3.5`}>
      <SheetPortrait />
      <div className="w-[290px] shrink-0">
        <TextValue
          label={text.identity.name}
          value={sheet.texts.name ?? ""}
          editing={editing}
          onCommit={save("name")}
          maxLength={80}
          className="text-ink-bright block truncate text-[40px] leading-[48px] font-bold [text-shadow:0_0_14px_rgb(255_90_20/0.25)]"
        />
        {character.npc == null ? (
          <p className="text-ink-muted pl-0.5 text-[15px] font-medium italic">
            {text.ownerLine} {character.owner_name}
          </p>
        ) : (
          <NpcCategoryLine character={character} />
        )}
      </div>
      <dl className="grid flex-1 grid-cols-[1.2fr_1.2fr_0.8fr_0.8fr_1.4fr] gap-x-5">
        {FIELDS.map((field) => (
          <div key={field} className="min-w-0">
            <dt className={SMALL_LABEL}>{text.identity[field]}</dt>
            <dd className="mt-1.5">
              <TextValue
                label={text.identity[field]}
                value={sheet.texts[field] ?? ""}
                editing={editing}
                onCommit={save(field)}
                maxLength={120}
                className="text-ink block truncate text-lg leading-[22px] font-semibold"
              />
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
