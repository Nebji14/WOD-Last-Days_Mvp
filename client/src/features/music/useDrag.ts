"use client";

/**
 * Déplacement d'un panneau flottant par sa poignée, sans sortir de la fenêtre.
 *
 * La position passe par le DOM et non par un attribut `style`, interdit par la
 * politique de sécurité du contenu.
 */
import { type PointerEvent, type RefObject, useCallback, useRef } from "react";

interface DragStart {
  readonly pointerX: number;
  readonly pointerY: number;
  readonly rect: DOMRect;
}

export interface DragHandlers {
  readonly onPointerDown: (event: PointerEvent<HTMLElement>) => void;
  readonly onPointerMove: (event: PointerEvent<HTMLElement>) => void;
  readonly onPointerUp: () => void;
  readonly onPointerCancel: () => void;
}

interface Drag {
  readonly handlers: DragHandlers;
  /** Remet le panneau à sa place d'origine. */
  readonly reset: () => void;
}

export function useDrag(panel: RefObject<HTMLElement | null>): Drag {
  const offset = useRef({ x: 0, y: 0 });
  const start = useRef<DragStart | null>(null);

  const clamp = (value: number, min: number, max: number): number =>
    Math.min(Math.max(value, min), Math.max(min, max));

  const reset = useCallback(() => {
    offset.current = { x: 0, y: 0 };
    if (panel.current !== null) {
      panel.current.style.translate = "";
    }
  }, [panel]);

  const handlers: DragHandlers = {
    onPointerDown: (event) => {
      if (panel.current === null) {
        return;
      }
      event.currentTarget.setPointerCapture(event.pointerId);
      start.current = {
        pointerX: event.clientX,
        pointerY: event.clientY,
        rect: panel.current.getBoundingClientRect(),
      };
    },
    onPointerMove: (event) => {
      const from = start.current;
      if (from === null || panel.current === null) {
        return;
      }
      const { rect } = from;
      const left = clamp(
        rect.left + event.clientX - from.pointerX,
        0,
        window.innerWidth - rect.width,
      );
      const top = clamp(
        rect.top + event.clientY - from.pointerY,
        0,
        window.innerHeight - rect.height,
      );
      const current = panel.current.getBoundingClientRect();
      offset.current = {
        x: offset.current.x + left - current.left,
        y: offset.current.y + top - current.top,
      };
      panel.current.style.translate = `${offset.current.x}px ${offset.current.y}px`;
    },
    onPointerUp: () => {
      start.current = null;
    },
    onPointerCancel: () => {
      start.current = null;
    },
  };

  return { handlers, reset };
}
