"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams, useParams, useRouter } from "next/navigation";
import { getQueuePosition, getEventStats } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import ParticleTunnel from "@/components/ParticleTunnel/ParticleTunnel";
import QueueStatus from "@/components/QueueStatus/QueueStatus";
import LiveStats from "@/components/LiveStats/LiveStats";
import TurnNotification from "@/components/TurnNotification/TurnNotification";
import SimulationHUD from "@/components/SimulationHUD/SimulationHUD";
import type { QueuePositionResponse, EventStats } from "@/types";
import styles from "./page.module.css";

export default function QueuePage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const eventId = params.eventId as string;
  const router = useRouter();

  const isSimMode = searchParams.get("sim") === "true";
  const urlUserId = searchParams.get("user_id");

  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [position, setPosition] = useState<QueuePositionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [turnTTL, setTurnTTL] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [artificialLoading, setArtificialLoading] = useState(true);
  const [stats, setStats] = useState<EventStats | null>(null);
  const [waitingBehind, setWaitingBehind] = useState(0);

  // Forzar scroll al tope instantáneamente al entrar
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Timer de carga artificial de 4 segundos
  useEffect(() => {
    const timer = setTimeout(() => {
      setArtificialLoading(false);
    }, 4000);
    return () => clearTimeout(timer);
  }, []);



  // Particle tunnel animation state
  const [burst, setBurst] = useState(false);
  const [hyperspace, setHyperspace] = useState(false);
  const prevPositionRef = useRef<number | null>(null);
  const initialPositionRef = useRef<number | null>(null);
  const burstKeyRef = useRef(0);

  // Conectar al WebSocket para recibir actualizaciones en tiempo real
  const { lastMessage, isConnected } = useWebSocket(eventId);

  // Leer el user_id
  useEffect(() => {
    if (isSimMode && urlUserId) {
      setUserId(urlUserId);
      setUserName("User Simulador");
    } else {
      const storedId = localStorage.getItem("vq_user_id");
      const storedFirst = localStorage.getItem("vq_first_name") || "";
      const storedLast = localStorage.getItem("vq_last_name") || "";
      setUserId(storedId);
      setUserName(`${storedFirst} ${storedLast}`.trim());
    }
  }, [isSimMode, urlUserId]);

  // Función para consultar la posición actual al backend
  const fetchPosition = useCallback(async () => {
    if (!userId) return;
    try {
      const data = await getQueuePosition(userId, eventId);
      setPosition(data);
      setLoading(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      // Si el backend dice que el usuario no está en la fila,
      // es porque el Worker ya lo procesó (le dio permiso para comprar).
      if (message.includes("no está en la")) {
        setIsMyTurn(true);
        setTurnTTL(120);
      } else {
        setError(message || "Error al consultar posición");
      }
      setLoading(false);
    }
  }, [userId, eventId]);

  // Función para consultar las estadísticas del evento
  const fetchStats = useCallback(async () => {
    try {
      const data = await getEventStats(eventId);
      setStats(data.stats);
    } catch {
      // No bloquear si las stats fallan
    }
  }, [eventId]);

  // Consultar posición cuando el userId esté disponible
  useEffect(() => {
    if (userId) {
      fetchPosition();
      fetchStats();
    }
  }, [userId, fetchPosition, fetchStats]);

  // Reaccionar a los mensajes del WebSocket
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === "your_turn" && lastMessage.user_id === userId) {
      // Activate hyperspace effect before showing the turn card
      setHyperspace(true);
      setTimeout(() => {
        setIsMyTurn(true);
        setTurnTTL(lastMessage.ttl_seconds);
        setHyperspace(false);
      }, 2000);
    }

    if (lastMessage.type === "position_update") {
      fetchPosition();
      
      // Actualizar estadísticas en tiempo real — solo campos para SimulationHUD
      // LiveStats maneja internamente sus propias métricas (simStats) via lastMessage
      const msg = lastMessage as any;
      setStats((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          processed_count: (prev.processed_count || 0) + (msg.users_processed || 0),
          abandoned_count: (prev.abandoned_count || 0) + (msg.users_abandoned || 0),
          processed_rate: msg.processed_rate !== undefined ? msg.processed_rate : prev.processed_rate,
          throughput: msg.throughput !== undefined ? msg.throughput : prev.throughput,
          tech_logs: msg.tech_logs || prev.tech_logs,
        };
      });

      // Simulación normal: incrementar usuarios detrás (cosmético)
      if (!isSimMode) {
        setWaitingBehind(prev => prev + Math.floor(Math.random() * 4) + 1);
      }
    }
  }, [lastMessage, userId, fetchPosition]);

  // Trigger burst animation when position changes
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

  // Track initial position (set once when first position arrives)
  useEffect(() => {
    if (position && initialPositionRef.current === null) {
      initialPositionRef.current = position.position;
    }
  }, [position]);

  // Calculate speed multiplier based on how far user has advanced from initial position
  const speedMultiplier = (() => {
    if (hyperspace) return 6;
    const initial = initialPositionRef.current;
    if (!position || !initial || initial <= 1) return 0.8;
    // progress: 0 (just entered, at initial position) → 1 (position 1, about to be your turn)
    const progress = 1 - (position.position - 1) / (initial - 1);
    // Exponential curve: speed ramps up noticeably as you approach the front
    // Range: 0.8 (far) → 3.5 (about to be your turn)
    return 0.8 + Math.pow(Math.max(0, progress), 1.5) * 2.7;
  })();

  // Contador regresivo del tiempo para comprar
  useEffect(() => {
    if (!isMyTurn || turnTTL <= 0) return;
    const interval = setInterval(() => {
      setTurnTTL((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isMyTurn, turnTTL]);

  // Pantalla de carga (Datos + Artificial para mejor UX)
  if (loading || artificialLoading) {
    return (
      <>
        <ParticleTunnel
          speedMultiplier={2.5}
          burst={false}
          hyperspace={false}
        />
        <div className={styles.loadingContainer}>
          <div className={styles.loaderContent}>
            <p className={styles.syncText}>Sincronizando con el servidor...</p>
          </div>
          <div className={styles.spinner}></div>
        </div>
      </>
    );
  }

  if (!userId) {
    return (
      <div className={styles.container}>
        <p className={styles.error}>
          No se encontró tu identificación. Volvé al evento y entrá en la fila nuevamente.
        </p>
      </div>
    );
  }

  // Pantalla cuando es el turno del usuario
  if (isMyTurn) {
    return (
      <div className={styles.container}>
        <TurnNotification
          userName={userName}
          turnTTL={turnTTL}
          onPurchase={() => router.push(`/compra/${eventId}`)}
          onCancel={() => router.push("/")}
          onViewEvents={() => router.push("/")}
        />
      </div>
    );
  }

  return (
    <>
      <ParticleTunnel
        speedMultiplier={speedMultiplier}
        burst={burst}
        hyperspace={hyperspace}
      />
      <div className={`${styles.container} ${isSimMode ? styles.simMode : ""}`}>
        {isSimMode && (
          <SimulationHUD
            processedCount={stats?.processed_count || 0}
            abandonedCount={stats?.abandoned_count || 0}
            processedRate={(stats as any)?.processed_rate || 0}
            throughput={(stats as any)?.throughput || 0}
            onStop={() => router.push("/?simulation=true")}
            onGoHome={() => router.push("/")}
          />
        )}

        <h1 className={styles.eventName}>
          {isSimMode ? "⚙️ Control de Simulación" : (userName ? `Hola ${userName}` : "Sala de espera")}
        </h1>
        <p className={styles.subtitle}>
          {isSimMode
            ? "La simulación está activa. Los usuarios están siendo procesados según la tasa configurada."
            : "Mantené esta página abierta. Te avisaremos cuando sea tu turno."}
        </p>

        <QueueStatus
          position={position}
          error={error}
          isConnected={isConnected}
          waitingBehind={waitingBehind}
        />

        {/* Estadísticas del evento */}
        {stats && (
          <LiveStats 
            stats={stats} 
            isSimMode={isSimMode} 
            lastMessage={lastMessage} 
            waitingBehind={waitingBehind} 
            eventId={eventId}
          />
        )}
      </div>
    </>
  );
}
