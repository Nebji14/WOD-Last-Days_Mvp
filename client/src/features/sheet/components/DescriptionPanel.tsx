"use client";

/**
 * [Panneau — Description et récit] du verso (05b) : état civil, apparence,
 * histoire et description. La taille physique n'est pas la Taille de jeu.
 */
import { setSheetField } from "@/features/characters/api";
import { labels } from "@/shared/i18n";

import { Panel, TextValue, useSheet } from "./primitives";

const SHORT_FIELDS = [
  "age",
  "height",
  "weight",
  "sex",
  "hair",
  "eyes",
  "origin",
  "nationality",
] as const;
const LONG_FIELDS = ["history", "description"] as const;
const FIELD_LABEL = "font-display text-gold text-[8px] font-bold tracking-[1.5px]";

export function DescriptionPanel() {
  const { sheet, editing, run } = useSheet();
  const text = labels.sheet.description;
  const save = (field: string) => (value: string) =>
    void run(() => setSheetField(sheet.id, field, value, sheet.texts[field] ?? ""));

  return (
    <Panel title={text.title}>
      <dl className="grid grid-cols-4 gap-x-2 gap-y-3">
        {SHORT_FIELDS.map((field) => (
          <div key={field} className="min-w-0">
            <dt className={FIELD_LABEL}>{text[field]}</dt>
            <dd className="mt-1">
              <TextValue
                label={text[field]}
                value={sheet.texts[field] ?? ""}
                editing={editing}
                onCommit={save(field)}
                maxLength={field === "origin" || field === "nationality" ? 120 : 60}
                className="text-ink block truncate text-base font-semibold"
              />
            </dd>
          </div>
        ))}
      </dl>
      {LONG_FIELDS.map((field) => (
        <div key={field} className="mt-4">
          <p className={FIELD_LABEL}>{text[field]}</p>
          <div className="mt-1.5">
            <TextValue
              label={text[field]}
              value={sheet.texts[field] ?? ""}
              editing={editing}
              onCommit={save(field)}
              maxLength={20000}
              multiline
              className="text-ink block min-h-[110px] text-base leading-snug font-medium"
            />
          </div>
        </div>
      ))}
    </Panel>
  );
}
