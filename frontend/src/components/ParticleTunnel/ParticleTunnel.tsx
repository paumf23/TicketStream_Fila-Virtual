"use client";

/**
 * ParticleTunnel.tsx — Animación Visual de la Cola (Túnel de Partículas)
 * 
 * Este componente renderiza un canvas con una animación de estilo "túnel hiperespacial".
 * Reacciona dinámicamente a la posición del usuario en la fila:
 * 1. La velocidad base aumenta a medida que el usuario avanza.
 * 2. El efecto 'burst' se dispara cuando hay un salto de posición.
 * 3. El efecto 'hyperspace' se activa cuando es el turno del usuario para comprar.
 */

import { useRef, useEffect, useCallback } from "react";
import styles from "./ParticleTunnel.module.css";

interface ParticleTunnelProps {
  /** Multiplicador de velocidad base: 0.3 = lento, 1 = normal, 5 = hiperspacio */
  speedMultiplier: number;
  /** Breve ráfaga de aceleración (ej. al cambiar de posición) */
  burst: boolean;
  /** Efecto de hiperspacio completo (cuando es tu turno) */
  hyperspace: boolean;
}

// ── Estructura de datos de la partícula ──
interface Particle {
  angle: number;
  distance: number;
  speed: number;
  length: number;
  hue: number;
  opacity: number;
  width: number;
}

const PARTICLE_COUNT = 140;
const BASE_SPEED = 2.0;

// Colores que coinciden con la paleta del proyecto
const PRIMARY_HUE = 252;    // #6C5CE7
const SECONDARY_HUE = 177;  // #00CEC9

function createParticle(maxRadius: number, spread: boolean = false): Particle {
  const hue = Math.random() > 0.5 ? PRIMARY_HUE : SECONDARY_HUE;
  return {
    angle: Math.random() * Math.PI * 2,
    distance: spread ? Math.random() * maxRadius : Math.random() * 8 + 1,
    speed: 0.4 + Math.random() * 0.6,
    length: 0.6 + Math.random() * 0.4,
    hue,
    opacity: 0.4 + Math.random() * 0.5,
    width: 1.0 + Math.random() * 2.0,
  };
}

function resetParticle(p: Particle): void {
  p.angle = Math.random() * Math.PI * 2;
  p.distance = Math.random() * 6 + 1;
  p.speed = 0.4 + Math.random() * 0.6;
  p.length = 0.6 + Math.random() * 0.4;
  p.hue = Math.random() > 0.5 ? PRIMARY_HUE : SECONDARY_HUE;
  p.opacity = 0.4 + Math.random() * 0.5;
  p.width = 1.0 + Math.random() * 2.0;
}

export default function ParticleTunnel({
  speedMultiplier,
  burst,
  hyperspace,
}: ParticleTunnelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animFrameRef = useRef<number>(0);
  const currentSpeedRef = useRef(speedMultiplier);
  const burstEndRef = useRef(0);
  const hyperspaceFlashRef = useRef(0);

  // Rastrear la activación de la ráfaga (burst)
  useEffect(() => {
    if (burst) {
      burstEndRef.current = performance.now() + 1200;
    }
  }, [burst]);

  // Rastrear activación de hiperspacio — dispara destello visual
  useEffect(() => {
    if (hyperspace) {
      hyperspaceFlashRef.current = performance.now() + 600;
    }
  }, [hyperspace]);

  // Bucle de animación (loop)
  const animate = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const maxRadius = Math.sqrt(cx * cx + cy * cy);

    // Inicializar partículas en la primera ejecución
    if (particlesRef.current.length === 0) {
      particlesRef.current = Array.from({ length: PARTICLE_COUNT }, () =>
        createParticle(maxRadius, true)
      );
    }

    const particles = particlesRef.current;
    const now = performance.now();

    // ── Determinar la velocidad objetivo ──
    let targetSpeed = speedMultiplier;
    if (hyperspace) {
      targetSpeed = 6;
    } else if (now < burstEndRef.current) {
      targetSpeed = Math.max(speedMultiplier, 4.0);
    }

    // Interpolación suave (lerp) hacia la velocidad objetivo
    const lerpFactor = hyperspace ? 0.1 : 0.05;
    currentSpeedRef.current +=
      (targetSpeed - currentSpeedRef.current) * lerpFactor;
    const speed = currentSpeedRef.current;

    // ── Limpiar con rastro de desvanecimiento (trail) ──
    const fadeAlpha = hyperspace ? 0.04 : 0.08;
    ctx.fillStyle = `rgba(15, 15, 26, ${fadeAlpha})`;
    ctx.fillRect(0, 0, w, h);

    // ── Superposición de destello de hiperspacio ──
    if (now < hyperspaceFlashRef.current) {
      const flashProgress = 1 - (hyperspaceFlashRef.current - now) / 600;
      const flashAlpha = Math.sin(flashProgress * Math.PI) * 0.25;
      ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`;
      ctx.fillRect(0, 0, w, h);
    }

    // ── Actualizar y dibujar partículas ──
    for (const p of particles) {
      // Acelerar hacia afuera — las partículas cerca de los bordes se mueven más rápido
      const depthRatio = p.distance / maxRadius;
      const moveAmount =
        BASE_SPEED * speed * p.speed * (0.8 + depthRatio * 2.5);
      p.distance += moveAmount;

      // Reciclar la partícula si sale de los límites del canvas
      if (p.distance > maxRadius) {
        resetParticle(p);
        continue;
      }

      // Posición cartesiana final
      const x = cx + Math.cos(p.angle) * p.distance;
      const y = cy + Math.sin(p.angle) * p.distance;

      // Largo de la estela: crece con la distancia y la velocidad actual
      const streakMultiplier = hyperspace ? 6.0 : 1.8;
      const streakLength =
        moveAmount * (5 + depthRatio * 18) * p.length * streakMultiplier;
      const xTail = x - Math.cos(p.angle) * streakLength;
      const yTail = y - Math.sin(p.angle) * streakLength;

      // La opacidad aumenta gradualmente con la distancia del centro
      const alpha = p.opacity * (0.1 + depthRatio * 0.9);

      // Color: los tonos son más brillantes durante el hiperspacio
      const lightness = hyperspace
        ? 70 + depthRatio * 28
        : 55 + depthRatio * 20;
      const saturation = hyperspace ? 85 : 70;

      // Ancho de línea: se vuelve ligeramente más grueso en los bordes
      const lineWidth = p.width * (0.4 + depthRatio * 1.8);

      ctx.beginPath();
      ctx.moveTo(xTail, yTail);
      ctx.lineTo(x, y);
      ctx.strokeStyle = `hsla(${p.hue}, ${saturation}%, ${lightness}%, ${alpha})`;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = "round";
      ctx.stroke();
    }

    // ── Resplandor central ──
    const glowRadius = hyperspace ? 150 : 80;
    const glowAlpha = hyperspace ? 0.2 : 0.06;
    const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowRadius);
    gradient.addColorStop(
      0,
      `hsla(${PRIMARY_HUE}, 75%, 65%, ${glowAlpha})`
    );
    gradient.addColorStop(1, "transparent");
    ctx.fillStyle = gradient;
    ctx.fillRect(
      cx - glowRadius,
      cy - glowRadius,
      glowRadius * 2,
      glowRadius * 2
    );

    animFrameRef.current = requestAnimationFrame(animate);
  }, [speedMultiplier, hyperspace]);

  // Manejar el redimensionamiento del canvas al cambiar el tamaño de la ventana
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  // Iniciar / detener el bucle de animación principal
  useEffect(() => {
    animFrameRef.current = requestAnimationFrame(animate);
    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [animate]);

  return <canvas ref={canvasRef} className={styles.tunnelCanvas} />;
}
