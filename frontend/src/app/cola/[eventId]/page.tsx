"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { getQueuePosition, getEventStats } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import ParticleTunnel from "@/components/ParticleTunnel/ParticleTunnel";
import type { QueuePositionResponse, EventStats } from "@/types";
import styles from "./page.module.css";

export default function QueuePage() {
  const params = useParams();
  const eventId = params.eventId as string;
  const router = useRouter();

  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [position, setPosition] = useState<QueuePositionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [turnTTL, setTurnTTL] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<EventStats | null>(null);

  // Particle tunnel animation state
  const [burst, setBurst] = useState(false);
  const [hyperspace, setHyperspace] = useState(false);
  const prevPositionRef = useRef<number | null>(null);
  const initialPositionRef = useRef<number | null>(null);
  const burstKeyRef = useRef(0);

  // Conectar al WebSocket para recibir actualizaciones en tiempo real
  const { lastMessage, isConnected } = useWebSocket(eventId);

  // Leer el user_id de localStorage solo en el navegador (evita hydration error)
  useEffect(() => {
    const storedId = localStorage.getItem("vq_user_id");
    const storedFirst = localStorage.getItem("vq_first_name") || "";
    const storedLast = localStorage.getItem("vq_last_name") || "";
    setUserId(storedId);
    setUserName(`${storedFirst} ${storedLast}`.trim());
  }, []);

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
      fetchStats();
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

  // Pantalla de carga inicial
  if (loading) {
    return (
      <div className={styles.container}>
        <p className={styles.waiting}>Cargando...</p>
      </div>
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
    const minutes = Math.floor(turnTTL / 60);
    const seconds = turnTTL % 60;
    const isExpired = turnTTL <= 0;

    return (
      <div className={styles.container}>
        {isExpired ? (
          <div className={styles.expiredCard}>
            <span className={styles.turnIcon}>⏰</span>
            <h1 className={styles.expiredTitle}>Se agotó el tiempo</h1>
            <p className={styles.expiredMessage}>
              El tiempo para completar tu compra ha expirado. Volvé a elegir un evento para reiniciar el proceso.
            </p>
            <button
              className={styles.expiredButton}
              onClick={() => router.push("/")}
            >
              Ver eventos disponibles
            </button>
          </div>
        ) : (
          <div className={styles.turnCard}>
            <span className={styles.turnIcon}>🎉</span>
            <h1 className={styles.turnTitle}>¡Es tu turno, {userName}!</h1>
            <p className={styles.turnMessage}>
              Tenés tiempo limitado para completar tu compra.
            </p>
            <button
              className={styles.turnButton}
              onClick={() => router.push(`/compra/${eventId}`)}
            >
              Ir a comprar 🎫
            </button>
            <button
              className={styles.regretButton}
              onClick={() => router.push("/")}
            >
              Me arrepentí
            </button>
            <p className={styles.turnTimer}>
              Tiempo restante: {minutes}:{seconds.toString().padStart(2, "0")}
            </p>
          </div>
        )}
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
    <div className={styles.container}>
      <h1 className={styles.eventName}>
        {userName ? `Hola ${userName}` : "Sala de espera"}
      </h1>
      <p className={styles.subtitle}>
        Mantené esta página abierta. Te avisaremos cuando sea tu turno.
      </p>

      <div className={styles.card}>
        <span className={styles.positionLabel}>Tu posición en la fila</span>

        {position ? (
          <>
            <span className={styles.positionNumber}>{position.position}</span>

            <div className={styles.progressSection}>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{
                    width: `${Math.max(
                      5,
                      100 - (position.position / Math.max(1, position.queue_length)) * 100
                    )}%`,
                  }}
                />
              </div>
              <span className={styles.progressText}>
                {position.queue_length} personas en la fila
              </span>
            </div>

            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <div className={styles.infoLabel}>Personas adelante</div>
                <div className={styles.infoValue}>{position.position - 1}</div>
              </div>
              <div className={styles.infoItem}>
                <div className={styles.infoLabel}>Espera estimada</div>
                <div className={styles.infoValue}>{position.estimated_wait}</div>
              </div>
            </div>
          </>
        ) : error ? (
          <p className={styles.error}>{error}</p>
        ) : (
          <p className={styles.waiting}>Cargando posición...</p>
        )}

        <div className={styles.connectionStatus}>
          <span
            className={`${styles.dot} ${
              isConnected ? styles.dotConnected : styles.dotDisconnected
            }`}
          />
          <span>{isConnected ? "Conectado en tiempo real" : "Reconectando..."}</span>
        </div>
      </div>

      {/* Estadísticas del evento */}
      {stats && (
        <div className={styles.statsCard}>
          <p className={styles.statsTitle}>📊 Estadísticas en vivo</p>
          <div className={styles.statsGrid}>
            <div className={styles.statItem}>
              <div className={styles.statValue}>{stats.tickets_sold}</div>
              <div className={styles.statLabel}>Tickets vendidos</div>
            </div>
            <div className={styles.statItem}>
              <div className={`${styles.statValue} ${styles.statValueHighlight}`}>
                ${stats.revenue.toLocaleString("es-AR")}
              </div>
              <div className={styles.statLabel}>Recaudación</div>
            </div>
            <div className={styles.statItem}>
              <div className={styles.statValue}>{stats.queue_length}</div>
              <div className={styles.statLabel}>En la fila</div>
            </div>
            <div className={styles.occupancyBar}>
              <div className={styles.occupancyHeader}>
                <span className={styles.statLabel}>Ocupación</span>
                <span className={styles.statValue}>
                  {stats.occupancy_percentage.toFixed(1)}%
                </span>
              </div>
              <div className={styles.occupancyTrack}>
                <div
                  className={styles.occupancyFill}
                  style={{
                    width: `${Math.min(100, stats.occupancy_percentage)}%`,
                    backgroundColor:
                      stats.occupancy_percentage > 80
                        ? "var(--color-danger)"
                        : stats.occupancy_percentage > 50
                        ? "var(--color-warning)"
                        : "var(--color-success)",
                  }}
                />
              </div>
            </div>
            <div className={styles.statItem}>
              <div className={styles.statValue}>{stats.peak_queue_length}</div>
              <div className={styles.statLabel}>Pico máximo fila</div>
            </div>
            <div className={styles.statItem}>
              <div className={styles.statValue}>
                {stats.avg_wait_time_seconds
                  ? `${Math.round(stats.avg_wait_time_seconds)}s`
                  : "—"}
              </div>
              <div className={styles.statLabel}>Espera promedio</div>
            </div>
            <div className={styles.statItem}>
              <div className={styles.statValue}>{stats.remaining_capacity}</div>
              <div className={styles.statLabel}>Entradas restantes</div>
            </div>
          </div>
        </div>
      )}

      <button
        className={styles.exitQueueButton}
        onClick={() => router.push("/")}
      >
        Salir de la fila
      </button>
    </div>
    </>
  );
}
