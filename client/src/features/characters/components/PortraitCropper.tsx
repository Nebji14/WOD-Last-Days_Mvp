"use client";

/**
 * Cadrage d'une photo : on la déplace à la souris, au doigt ou aux flèches, et
 * on zoome avec la molette ou le curseur. Le cercle montre ce qui sera affiché.
 *
 * Tout est dessiné sur un canvas : la politique de sécurité interdit de
 * positionner l'image par un style en ligne.
 */
import { type KeyboardEvent, type PointerEvent, useEffect, useRef } from "react";

import { labels } from "@/shared/i18n";

import { MAX_ZOOM, moveCrop, type SquareCrop, zoomCrop, zoomOf } from "../portraitCrop";

const VIEW_SIZE = 600;
const WHEEL_STEP = 1.1;
const KEY_STEP = 0.05;
const KEY_MOVES: Readonly<Record<string, readonly [number, number]>> = {
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
  ArrowUp: [0, -1],
  ArrowDown: [0, 1],
};

interface PortraitCropperProps {
  readonly bitmap: ImageBitmap;
  readonly crop: SquareCrop;
  readonly onCrop: (crop: SquareCrop) => void;
}

function draw(canvas: HTMLCanvasElement, bitmap: ImageBitmap, crop: SquareCrop): void {
  const context = canvas.getContext("2d");
  if (context === null) {
    return;
  }
  context.clearRect(0, 0, VIEW_SIZE, VIEW_SIZE);
  context.drawImage(bitmap, crop.x, crop.y, crop.side, crop.side, 0, 0, VIEW_SIZE, VIEW_SIZE);
  // Assombrit ce qui restera hors du médaillon.
  context.beginPath();
  context.rect(0, 0, VIEW_SIZE, VIEW_SIZE);
  context.arc(VIEW_SIZE / 2, VIEW_SIZE / 2, VIEW_SIZE / 2 - 4, 0, Math.PI * 2, true);
  context.fillStyle = "rgb(5 2 2 / 0.7)";
  context.fill();
  context.beginPath();
  context.arc(VIEW_SIZE / 2, VIEW_SIZE / 2, VIEW_SIZE / 2 - 4, 0, Math.PI * 2);
  context.strokeStyle = "#c9b06a";
  context.lineWidth = 4;
  context.stroke();
}

export function PortraitCropper({ bitmap, crop, onCrop }: PortraitCropperProps) {
  const text = labels.sheet.portrait;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dragRef = useRef<{ readonly x: number; readonly y: number } | null>(null);
  const zoom = zoomOf(crop, bitmap);

  useEffect(() => {
    if (canvasRef.current !== null) {
      draw(canvasRef.current, bitmap, crop);
    }
  }, [bitmap, crop]);

  // Écouteur natif : React n'autorise pas à bloquer le défilement de la page.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas === null) {
      return;
    }
    const onWheel = (event: WheelEvent): void => {
      event.preventDefault();
      const factor = event.deltaY < 0 ? WHEEL_STEP : 1 / WHEEL_STEP;
      onCrop(zoomCrop(crop, zoomOf(crop, bitmap) * factor, bitmap));
    };
    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => canvas.removeEventListener("wheel", onWheel);
  }, [bitmap, crop, onCrop]);

  function startDrag(event: PointerEvent<HTMLCanvasElement>): void {
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { x: event.clientX, y: event.clientY };
  }

  function drag(event: PointerEvent<HTMLCanvasElement>): void {
    const from = dragRef.current;
    if (from === null) {
      return;
    }
    // La photo suit le pointeur : le cadre va donc dans l'autre sens.
    const ratio = crop.side / event.currentTarget.clientWidth;
    dragRef.current = { x: event.clientX, y: event.clientY };
    onCrop(
      moveCrop(crop, (from.x - event.clientX) * ratio, (from.y - event.clientY) * ratio, bitmap),
    );
  }

  function endDrag(): void {
    dragRef.current = null;
  }

  function moveWithKeys(event: KeyboardEvent<HTMLCanvasElement>): void {
    const move = KEY_MOVES[event.key];
    if (move === undefined) {
      return;
    }
    event.preventDefault();
    const step = crop.side * KEY_STEP;
    onCrop(moveCrop(crop, move[0] * step, move[1] * step, bitmap));
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <canvas
        ref={canvasRef}
        width={VIEW_SIZE}
        height={VIEW_SIZE}
        tabIndex={0}
        role="img"
        aria-label={text.cropLabel}
        onPointerDown={startDrag}
        onPointerMove={drag}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        onKeyDown={moveWithKeys}
        className="border-line focus-visible:outline-gold aspect-square w-full max-w-[300px] cursor-grab touch-none rounded-xs border active:cursor-grabbing"
      />
      <p className="text-ink-muted text-center text-[15px] italic">{text.cropHint}</p>
      <label className="text-ink-muted flex w-full max-w-[300px] items-center gap-3 text-[15px]">
        {text.zoom}
        <input
          type="range"
          min={1}
          max={MAX_ZOOM}
          step={0.01}
          value={zoom}
          onChange={(event) => onCrop(zoomCrop(crop, Number(event.target.value), bitmap))}
          className="accent-gold h-8 min-w-0 flex-1 cursor-pointer"
        />
      </label>
    </div>
  );
}
