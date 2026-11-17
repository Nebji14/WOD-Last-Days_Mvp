"use client";

/**
 * [Arborescence des catégories] de l'outil PNJ (04c).
 *
 * « Tous les PNJ », puis catégories ▾ / ▸ et sous-catégories en retrait, avec
 * le nombre de PNJ, sous-catégories comprises. Catégorie sélectionnée : bordure
 * or. Au survol ou au clavier : Renommer, Supprimer (04c-I2).
 */
import { labels } from "@/shared/i18n";
import { childrenOf } from "@/shared/tree";
import { InlineName } from "@/shared/ui/InlineName";

import type { NpcCategory } from "../api";

const NAME_MAX = 60;
const INDENT = ["pl-2", "pl-7", "pl-12", "pl-[4.25rem]"] as const;
const ROW_ACTION = "cursor-pointer px-1 text-sm hover:brightness-125";

interface CategoryTreeProps {
  readonly categories: readonly NpcCategory[];
  readonly counts: ReadonlyMap<string, number>;
  readonly total: number;
  readonly selectedId: string | null;
  readonly expanded: ReadonlySet<string>;
  readonly renamingId: string | null;
  readonly onSelect: (categoryId: string | null) => void;
  readonly onToggle: (categoryId: string) => void;
  readonly onRenameStart: (categoryId: string) => void;
  readonly onRename: (categoryId: string, name: string) => void;
  readonly onRenameEnd: () => void;
  readonly onDelete: (category: NpcCategory) => void;
}

export function CategoryTree(props: CategoryTreeProps) {
  const { categories, counts, selectedId } = props;
  const text = labels.npcsTool;

  const frame = (id: string | null) =>
    `group flex h-9 w-full items-center gap-2 rounded-xs border pr-2 text-left text-[18px] ${
      selectedId === id ? "border-gold bg-[#1e1813]" : "border-transparent hover:bg-[#1a1511]"
    }`;

  const renderLevel = (parentId: string | null, depth: number) =>
    childrenOf(categories, parentId).map((category) => {
      const hasChildren = categories.some((c) => c.parentId === category.id);
      const isOpen = props.expanded.has(category.id);
      return (
        <li key={category.id}>
          <div className={`${frame(category.id)} ${INDENT[Math.min(depth, INDENT.length - 1)]}`}>
            <button
              type="button"
              aria-label={isOpen ? text.collapse : text.expand}
              aria-expanded={isOpen}
              disabled={!hasChildren}
              onClick={() => props.onToggle(category.id)}
              className="text-ink w-3 shrink-0 cursor-pointer text-[11px] disabled:invisible"
            >
              {isOpen ? "▼" : "▶"}
            </button>
            {props.renamingId === category.id ? (
              <InlineName
                initial={category.name}
                label={text.categoryNameLabel}
                maxLength={NAME_MAX}
                onSubmit={(name) => props.onRename(category.id, name)}
                onCancel={props.onRenameEnd}
                className="h-7 min-w-0 flex-1 text-[16px]"
              />
            ) : (
              <button
                type="button"
                onClick={() => props.onSelect(category.id)}
                className={`min-w-0 flex-1 cursor-pointer truncate text-left ${
                  depth > 0 ? "text-ink-muted" : "text-ink"
                }`}
              >
                {category.name} · {counts.get(category.id) ?? 0}
              </button>
            )}
            <span className="hidden shrink-0 group-focus-within:flex group-hover:flex">
              <button
                type="button"
                aria-label={`${text.rename} ${category.name}`}
                title={text.rename}
                onClick={() => props.onRenameStart(category.id)}
                className={`${ROW_ACTION} text-gold`}
              >
                ✎
              </button>
              <button
                type="button"
                aria-label={`${text.delete} ${category.name}`}
                title={text.delete}
                onClick={() => props.onDelete(category)}
                className={`${ROW_ACTION} text-danger`}
              >
                ✕
              </button>
            </span>
          </div>
          {isOpen && hasChildren && <ul>{renderLevel(category.id, depth + 1)}</ul>}
        </li>
      );
    });

  return (
    <ul className="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto">
      <li>
        <button
          type="button"
          onClick={() => props.onSelect(null)}
          className={`${frame(null)} pl-2`}
        >
          <span className="text-ink">
            {text.allNpcs} · {props.total}
          </span>
        </button>
      </li>
      {renderLevel(null, 0)}
    </ul>
  );
}
