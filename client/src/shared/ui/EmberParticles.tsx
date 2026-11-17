"use client";

/**
 * Particules d'arrière-plan : braises cuivrées qui montent en ondulant, avec
 * quelques cendres grises.
 *
 * Rendu sur un canvas, sans bibliothèque externe. Si l'utilisateur a demandé
 * moins d'animations, les particules sont dessinées une fois et restent figées.
 */
import { useEffect, useRef } from "react";

const EMBER_COLORS = ["255, 160, 70", "255, 122, 30", "214, 110, 50"] as const;
const ASH_COLOR = "138, 129, 122";
/** Surface d'écran par particule, en pixels CSS, selon la densité demandée. */
const AREA_PER_PARTICLE = { normal: 22_000, sparse: 60_000 } as const;
const ASH_RATIO = 0.25;
const MAX_FRAME_SECONDS = 0.05;

interface Particle {
  x: number;
  y: number;
  radius: number;
  speed: number;
  swayAmplitude: number;
  swaySpeed: number;
  phase: number;
  alpha: number;
  color: string;
}

function createParticle(width: number, height: number): Particle {
  const isAsh = Math.random() < ASH_RATIO;
  return {
    x: Math.random() * width,
    y: Math.random() * height,
    radius: isAsh ? 0.5 + Math.random() * 0.8 : 0.7 + Math.random() * 1.9,
    speed: 6 + Math.random() * 22,
    swayAmplitude: 6 + Math.random() * 18,
    swaySpeed: 0.3 + Math.random() * 0.9,
    phase: Math.random() * Math.PI * 2,
    alpha: isAsh ? 0.2 + Math.random() * 0.2 : 0.55 + Math.random() * 0.45,
    color: isAsh
      ? ASH_COLOR
      : (EMBER_COLORS[Math.floor(Math.random() * EMBER_COLORS.length)] ?? EMBER_COLORS[0]),
  };
}

function drawParticle(context: CanvasRenderingContext2D, particle: Particle, time: number): void {
  const x =
    particle.x + Math.sin(time * particle.swaySpeed + particle.phase) * particle.swayAmplitude;
  const flicker = 0.75 + 0.25 * Math.sin(time * 3 * particle.swaySpeed + particle.phase);
  const glowRadius = particle.radius * 2;
  const gradient = context.createRadialGradient(x, particle.y, 0, x, particle.y, glowRadius);
  gradient.addColorStop(0, `rgba(${particle.color}, ${particle.alpha * flicker})`);
  gradient.addColorStop(0.45, `rgba(${particle.color}, ${particle.alpha * flicker * 0.7})`);
  gradient.addColorStop(1, `rgba(${particle.color}, 0)`);
  context.fillStyle = gradient;
  context.beginPath();
  context.arc(x, particle.y, glowRadius, 0, Math.PI * 2);
  context.fill();
}

interface EmberParticlesProps {
  /** Classes de positionnement et d'opacité du canvas. */
  readonly className?: string;
  /** `sparse` : braises discrètes de la table de jeu. */
  readonly density?: keyof typeof AREA_PER_PARTICLE;
}

export function EmberParticles({ className = "", density = "normal" }: EmberParticlesProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) {
      return;
    }
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let particles: Particle[] = [];
    let width = 0;
    let height = 0;
    let frame = 0;
    let previous = performance.now();

    const render = (time: number): void => {
      context.clearRect(0, 0, width, height);
      particles.forEach((particle) => drawParticle(context, particle, time));
    };

    const resize = (): void => {
      const ratio = window.devicePixelRatio || 1;
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      const count = Math.round((width * height) / AREA_PER_PARTICLE[density]);
      particles = Array.from({ length: count }, () => createParticle(width, height));
      if (reducedMotion) {
        render(0);
      }
    };

    const tick = (now: number): void => {
      const elapsed = Math.min((now - previous) / 1000, MAX_FRAME_SECONDS);
      previous = now;
      for (const particle of particles) {
        particle.y -= particle.speed * elapsed;
        if (particle.y < -12) {
          particle.y = height + 12;
          particle.x = Math.random() * width;
        }
      }
      render(now / 1000);
      frame = requestAnimationFrame(tick);
    };

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();
    if (!reducedMotion) {
      frame = requestAnimationFrame(tick);
    }
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [density]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
    />
  );
}
