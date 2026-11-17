"use client";

/**
 * Panneaux Santé et Volonté du recto.
 *
 * Les blessures et la volonté disponible bougent pendant la partie : elles se
 * modifient à tout moment. Les maximums ne changent qu'avec la progression du
 * personnage : ils se modifient en mode modification. Le serveur garde la
 * piste de blessures rangée par gravité et refuse tout dépassement. Pour un
 * PNJ, les maximums sont « fixés par le MJ », sans base calculée.
 */
import { changeWounds, setSheetField, type WoundSymbol } from "@/features/characters/api";
import { fill, labels } from "@/shared/i18n";

import { NumberValue, Panel, useSheet } from "./primitives";

const WOUND_STYLE: Record<string, string> = {
  "*": "border-copper bg-[#322218] text-copper-text",
  X: "border-copper-deep bg-[#251b15] text-copper",
  "/": "border-ink-muted bg-field text-ink",
};
const ACTION =
  "border-line bg-panel font-display text-ink hover:border-gold cursor-pointer rounded-xs border px-2 py-1 text-[9px] font-bold tracking-[1px]";
const CAPACITY = "text-ink-muted flex items-center gap-1.5 text-sm font-medium italic";

function freeBoxesLabel(free: number): string {
  const text = labels.sheet.health;
  if (free === 0) {
    return text.noneFree;
  }
  return free === 1 ? text.oneFree : fill(text.free, { count: free });
}

/** Libellé devant le maximum : base calculée, ou « fixée par le MJ » pour un PNJ. */
function capacityLabel(isNpc: boolean, base: number): string {
  return isNpc ? labels.npcSheet.fixedByGm : fill(labels.sheet.health.capacity, { base });
}

export function HealthPanel() {
  const { character, sheet, editing, run } = useSheet();
  const text = labels.sheet.health;
  const capacity = sheet.effective.health_max;
  const wounds = sheet.wound_track;
  const boxes = Array.from({ length: capacity }, (_, index) => wounds[index] ?? "");
  const act = (action: "add" | "heal" | "worsen", wound: WoundSymbol | null) => () =>
    void run(() => changeWounds(sheet.id, action, wound, wounds));
  const worsenable: WoundSymbol | null = wounds.includes("/")
    ? "/"
    : wounds.includes("X")
      ? "X"
      : null;

  return (
    <Panel
      title={text.title}
      aside={
        <span className={CAPACITY}>
          {capacityLabel(character.npc != null, sheet.base.health_max)}
          <NumberValue
            label={text.title}
            value={capacity}
            editing={editing}
            min={1}
            max={30}
            onCommit={(value) =>
              void run(() => setSheetField(sheet.id, "health_max", value, capacity))
            }
          />
        </span>
      }
    >
      <div role="img" aria-label={`${text.title} : ${wounds.length} / ${capacity}`}>
        <div aria-hidden="true" className="flex flex-wrap gap-[7px]">
          {boxes.map((wound, index) => (
            <span
              key={index}
              className={`font-track flex size-[26px] items-center justify-center border text-lg leading-none font-bold ${
                WOUND_STYLE[wound] ?? "border-line bg-panel"
              }`}
            >
              {wound}
            </span>
          ))}
        </div>
      </div>
      <p className="text-ink-muted mt-3 text-[15px] font-medium italic">
        {text.track} {wounds ? wounds.split("").join(" ") : text.empty} ·{" "}
        {freeBoxesLabel(capacity - wounds.length)}
      </p>
      <div className="mt-2.5 flex flex-wrap gap-1.5">
        <button type="button" onClick={act("add", "/")} className={ACTION}>
          {text.addBashing}
        </button>
        <button type="button" onClick={act("add", "X")} className={ACTION}>
          {text.addLethal}
        </button>
        <button type="button" onClick={act("add", "*")} className={ACTION}>
          {text.addAggravated}
        </button>
        <button
          type="button"
          onClick={act("heal", null)}
          disabled={wounds === ""}
          className={`${ACTION} disabled:cursor-not-allowed disabled:opacity-40`}
        >
          {text.heal}
        </button>
        <button
          type="button"
          onClick={act("worsen", worsenable)}
          disabled={worsenable === null}
          className={`${ACTION} disabled:cursor-not-allowed disabled:opacity-40`}
        >
          {text.worsen}
        </button>
      </div>
    </Panel>
  );
}

export function WillpowerPanel() {
  const { character, sheet, editing, run } = useSheet();
  const text = labels.sheet.willpower;
  const max = sheet.effective.willpower_max;
  const current = sheet.willpower_current;
  const setCurrent = (value: number) => () =>
    void run(() => setSheetField(sheet.id, "willpower_current", value, current));

  return (
    <Panel
      title={text.title}
      aside={
        <span className={CAPACITY}>
          {capacityLabel(character.npc != null, sheet.base.willpower_max)}
          <NumberValue
            label={text.title}
            value={max}
            editing={editing}
            min={0}
            max={30}
            onCommit={(value) =>
              void run(() => setSheetField(sheet.id, "willpower_max", value, max))
            }
          />
        </span>
      }
    >
      <div className="flex items-center justify-between gap-4">
        <span
          role="group"
          aria-label={fill(text.available, { current, max })}
          className="flex flex-wrap gap-1.5"
        >
          {Array.from({ length: max }, (_, index) => index + 1).map((rank) => {
            const dot = `size-[18px] rounded-full ${
              rank <= current ? "bg-gold" : "border-gold/70 border-[1.5px]"
            }`;
            return (
              <button
                key={rank}
                type="button"
                aria-label={`${text.title} ${rank}`}
                onClick={setCurrent(rank === current ? rank - 1 : rank)}
                className={`${dot} cursor-pointer hover:brightness-150`}
              />
            );
          })}
        </span>
        <span className="text-ink shrink-0 text-base font-semibold">
          {fill(text.available, { current, max })}
        </span>
      </div>
    </Panel>
  );
}
