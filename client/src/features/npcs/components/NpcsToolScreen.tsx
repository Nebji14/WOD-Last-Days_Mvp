"use client";

/**
 * Fenêtre détachée de l'outil PNJ du MJ (écran 04c, US-039 à US-043).
 *
 * À gauche [Panneau — Catégories], à droite [Panneau — PNJ de la catégorie] :
 * fil d'Ariane, compteur, [Bouton — Créer un PNJ] et grille des cartes. Pas de
 * recherche au MVP (US-044). Une feuille créée s'ouvre aussitôt en mode
 * modification (07-I5).
 */
import { useEffect, useState } from "react";

import type { NpcModel } from "@/features/characters/model";
import { errorLabel, fill, labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";
import { DetachedTitleBar } from "@/shared/ui/DetachedTitleBar";
import { openSheet } from "@/shared/windows/detached";

import {
  createCategory,
  createNpc,
  deleteCategory,
  deleteNpc,
  type NpcCard,
  type NpcCategory,
  renameCategory,
} from "../api";
import { categoryCounts, categoryLabel, npcsIn } from "../categories";
import { useNpcDirectory } from "../useNpcDirectory";
import { CategoryTree } from "./CategoryTree";
import { CreateNpcMenu } from "./CreateNpcMenu";
import { NpcCardItem } from "./NpcCardItem";

const MESSAGE = "text-ink-muted flex flex-1 items-center justify-center p-8 text-xl italic";

type Pending =
  | { readonly kind: "npc"; readonly npc: NpcCard }
  | { readonly kind: "category"; readonly category: NpcCategory };

export function NpcsToolScreen() {
  const { directory, errorCode, act } = useNpcDirectory();
  const text = labels.npcsTool;
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set());
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);

  useEffect(() => {
    document.title = text.windowTitle;
  }, [text.windowTitle]);

  const categories = directory?.categories ?? [];
  const npcs = directory?.npcs ?? [];
  const selected = categories.find((c) => c.id === selectedId) ?? null;
  const shown = npcsIn(npcs, categories, selected?.id ?? null);

  /** Crée « Nouvelle catégorie » dans la catégorie sélectionnée et met son nom en saisie. */
  const newCategory = async () => {
    const created: { id: string | null } = { id: null };
    const parentId = selected?.id ?? null;
    const done = await act(async () => {
      created.id = await createCategory(text.defaultCategoryName, parentId);
    });
    if (done && created.id !== null) {
      setExpanded((current) => new Set([...current, ...(parentId === null ? [] : [parentId])]));
      setRenamingId(created.id);
    }
  };

  const newNpc = (model: NpcModel) => {
    void act(async () => {
      const npc = await createNpc(model, selected?.id ?? null);
      openSheet(npc.id, true);
    });
  };

  const confirmDeletion = () => {
    if (pending?.kind === "npc") {
      void act(() => deleteNpc(pending.npc.id));
    } else if (pending?.kind === "category") {
      const parentId = pending.category.parentId;
      void act(() => deleteCategory(pending.category.id)).then((done) => {
        if (done && selectedId === pending.category.id) {
          setSelectedId(parentId);
        }
      });
    }
    setPending(null);
  };

  const count =
    selected === null
      ? fill(text.countAll, { count: shown.length })
      : fill(shown.length === 1 ? text.countOne : text.countMany, { count: shown.length });

  return (
    <div className="bg-night text-ink flex h-screen flex-col">
      <DetachedTitleBar title={text.windowTitle} subtitle={text.subtitle} closeLabel={text.close} />
      {errorCode !== null && (
        <p
          role="alert"
          className="border-blood-line bg-danger-panel text-danger-bright shrink-0 border-b px-8 py-2 text-[15px]"
        >
          {errorLabel(errorCode)}
        </p>
      )}
      {directory === null ? (
        <main className={MESSAGE}>{text.loading}</main>
      ) : (
        <main className="grid min-h-0 flex-1 grid-cols-[280px_minmax(0,1fr)] gap-6 p-8">
          <section
            aria-label={text.categories}
            className="border-line bg-panel flex min-h-0 flex-col gap-4 rounded-xs border px-3 py-5"
          >
            <h2 className="font-display text-gold px-2 text-[12px] font-bold tracking-[3px]">
              {text.categories}
            </h2>
            <CategoryTree
              categories={categories}
              counts={categoryCounts(npcs, categories)}
              total={npcs.length}
              selectedId={selectedId}
              expanded={expanded}
              renamingId={renamingId}
              onSelect={setSelectedId}
              onToggle={(id) =>
                setExpanded((current) => {
                  const next = new Set(current);
                  if (!next.delete(id)) next.add(id);
                  return next;
                })
              }
              onRenameStart={setRenamingId}
              onRename={(id, name) => {
                setRenamingId(null);
                void act(() => renameCategory(id, name));
              }}
              onRenameEnd={() => setRenamingId(null)}
              onDelete={(category) => setPending({ kind: "category", category })}
            />
            <button
              type="button"
              onClick={() => void newCategory()}
              className="border-line-strong font-display text-ink mx-2 h-10 shrink-0 cursor-pointer rounded-xs border text-[11px] font-bold tracking-[2.5px] hover:brightness-125"
            >
              {text.newCategory}
            </button>
          </section>

          <section className="border-line bg-panel flex min-h-0 flex-col gap-5 rounded-xs border px-6 py-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-display text-gold text-[13px] font-bold tracking-[3px] uppercase">
                  {selected === null ? text.allNpcs : categoryLabel(categories, selected.id)}
                </h2>
                <p className="text-ink-muted mt-1 text-sm italic">{count}</p>
              </div>
              <CreateNpcMenu onCreate={newNpc} />
            </div>
            {shown.length === 0 ? (
              <p className="text-ink-faint text-lg italic">{text.empty}</p>
            ) : (
              <ul className="grid min-h-0 grid-cols-2 content-start gap-4 overflow-y-auto pr-1">
                {shown.map((npc) => (
                  <NpcCardItem
                    key={npc.id}
                    npc={npc}
                    onDelete={() => setPending({ kind: "npc", npc })}
                  />
                ))}
              </ul>
            )}
          </section>
        </main>
      )}
      <ConfirmDialog
        open={pending !== null}
        title={pending?.kind === "category" ? text.deleteCategoryTitle : text.deleteNpcTitle}
        question={
          pending?.kind === "category"
            ? fill(text.deleteCategoryQuestion, { name: pending.category.name })
            : fill(text.deleteNpcQuestion, { name: pending?.npc.name ?? "" })
        }
        confirmLabel={text.confirmDelete}
        cancelLabel={text.cancel}
        onConfirm={confirmDeletion}
        onCancel={() => setPending(null)}
      />
    </div>
  );
}
