import { useState, useEffect, useRef } from "react";
import type { QueuePositionResponse } from "@/types";

export function useQueueAnimations(position: QueuePositionResponse | null, hyperspace: boolean) {
  const [burst, setBurst] = useState(false);
  const prevPositionRef = useRef<number | null>(null);
  const initialPositionRef = useRef<number | null>(null);
  const burstKeyRef = useRef(0);

  // Scroll to top on mount
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Disparar animación de choque (burst) cuando la posición en la fila mejora
  useEffect(() => {
    if (!position) return;
    const prevPos = prevPositionRef.current;
    if (prevPos !== null && position.position < prevPos) {
      burstKeyRef.current += 1;
      setBurst(true);
      const timer = setTimeout(() => setBurst(false), 1200);
      return () => clearTimeout(timer);
    }
    prevPositionRef.current = position.position;
  }, [position]);

  // Registrar la posición inicial para calcular el progreso visual
  useEffect(() => {
    if (position && initialPositionRef.current === null) {
      initialPositionRef.current = position.position;
    }
  }, [position]);

  // Calcular el multiplicador de velocidad del túnel basado en progreso
  const speedMultiplier = (() => {
    if (hyperspace) return 6;
    const initial = initialPositionRef.current;
    if (!position || !initial || initial <= 1) return 0.8;
    const progress = 1 - (position.position - 1) / (initial - 1);
    return 0.8 + Math.pow(Math.max(0, progress), 1.5) * 2.7;
  })();

  return { burst, speedMultiplier };
}
