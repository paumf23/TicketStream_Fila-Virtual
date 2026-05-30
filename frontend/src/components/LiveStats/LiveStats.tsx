"use client";

/**
 * LiveStats.tsx — Componente de Estadísticas en Tiempo Real
 * 
 * Este componente se encarga de mostrar las métricas del evento y de la cola.
 * Tiene una doble función:
 * 1. Para simulación normal (sin configuración): Muestra datos amigables como tiempo de espera y lugar en la fila.
 * 2. Para simulación avanzada (con configuración): Muestra telemetría técnica avanzada (recaudación, carga, logs del sistema).
 * 
 * Recibe actualizaciones constantes vía WebSocket para mantener la interfaz sincronizada sin recargar.
 */


import React, { useState, useEffect, useRef } from "react";
import type { EventStats, WsMessage } from "@/types";
import styles from "./LiveStats.module.css";

interface LiveStatsProps {
  stats: EventStats;
  isSimMode?: boolean;
  lastMessage?: WsMessage | null;
  waitingBehind?: number;
  eventId?: string;
}

export default function LiveStats({
  stats,
  isSimMode = false,
  lastMessage,
  waitingBehind = 0,
  eventId
}: LiveStatsProps) {
  // Estado dinámico interno para métricas estándar de la cola (actualizado vía WebSocket)
  const [dynamicStats, setDynamicStats] = useState({
    lastJump: stats.last_jump || 0,
    // Usuarios en compra en esta sesión (los que les llegó el turno ahora)
    usersInPurchase: 0,
  });

  // Métricas avanzadas de simulación — mantenidas internas a este módulo
  const [simStats, setSimStats] = useState<EventStats>(stats);
  const [displayLogs, setDisplayLogs] = useState<string[]>([]);
  const initialStatsLoaded = useRef(false);

  // Helper para colores de logs
  const getLogColor = (log: string) => {
    if (log.includes("[WEBSOCKET]")) return "#4CAF50"; // Verde
    if (log.includes("[REDIS]")) return "#2196F3"; // Azul
    if (log.includes("[WORKER]")) return "#E040FB"; // Violeta
    if (log.includes("[SYSTEM]")) return "#FFD700"; // Dorado
    if (log.includes("[NETWORK]")) return "#00F2FF"; // Cian
    return "rgba(255, 255, 255, 0.7)";
  };

  // Inicializar logs
  useEffect(() => {
    if (isSimMode) {
      setDisplayLogs([
        "[SISTEMA] Motor de monitoreo vinculado",
        "[REDIS] Conexión estable con shard_0",
        "[WEBSOCKET] Canal de telemetría abierto",
        "[SISTEMA] Escuchando eventos de tráfico...",
        "[SISTEMA] Buffer de telemetría inicializado",
        "[WEBSOCKET] Sincronización de reloj OK"
      ]);
    }
  }, [isSimMode]);

  // Procesar nuevos logs técnicos
  useEffect(() => {
    if (isSimMode && simStats.tech_logs && simStats.tech_logs.length > 0) {
      setDisplayLogs((prev) => {
        const combined = [...prev, ...simStats.tech_logs!];
        return combined.slice(-6); // Mostrar exactamente 6 líneas
      });
    }
  }, [simStats.tech_logs, isSimMode]);

  // Sincronizar stats iniciales cuando llegan de la API (solo la primera vez)
  useEffect(() => {
    setDynamicStats((prev) => ({
      lastJump: prev.lastJump,
      usersInPurchase: prev.usersInPurchase,
    }));
    if (!initialStatsLoaded.current) {
      setSimStats(stats);
      initialStatsLoaded.current = true;
    }
  }, [stats]);

  // Procesar mensajes del WebSocket internamente (lógica de telemetría)
  useEffect(() => {
    if (!lastMessage || lastMessage.type !== "position_update") return;

    const msg = lastMessage;

    if (isSimMode) {
      // ═══════════════════════════════════════════════════════════════════════════
      // BLOQUE: SIMULACIÓN AVANZADA (Telemetría Técnica)
      // ═══════════════════════════════════════════════════════════════════════════
      setSimStats((prev) => {
        const usersProcessed = msg.users_processed || 0;
        const usersAbandoned = msg.users_abandoned || 0;

        return {
          ...prev,
          processed_count: (prev.processed_count || 0) + usersProcessed,
          abandoned_count: (prev.abandoned_count || 0) + usersAbandoned,
          tickets_sold: (prev.tickets_sold || 0) + usersProcessed,
          throughput: typeof msg.throughput === "number" ? msg.throughput : prev.throughput,
          processed_rate: typeof msg.processed_rate === "number" ? msg.processed_rate : (prev.processed_rate || 0),
          incoming_rate: typeof msg.incoming_rate === "number" ? msg.incoming_rate : (prev.incoming_rate || 0),
          effort: typeof msg.effort === "number" ? msg.effort : prev.effort,
          last_jump: typeof msg.last_jump === "number" ? msg.last_jump : prev.last_jump,
          trend: typeof msg.trend === "number" ? msg.trend : prev.trend,
          tech_logs: msg.tech_logs || prev.tech_logs,
          revenue: typeof msg.revenue === "number" ? msg.revenue : prev.revenue,
          occupancy_percentage: typeof msg.occupancy_percentage === "number" ? msg.occupancy_percentage : prev.occupancy_percentage,
          remaining_capacity: typeof msg.remaining_capacity === "number"
            ? msg.remaining_capacity
            : (prev.remaining_capacity - usersProcessed),
        };
      });
    } else {
      // ═══════════════════════════════════════════════════════════════════════════
      // BLOQUE: SIMULACIÓN NORMAL (Métricas de Usuario)
      // ══════════════════════════════════════════════════════════════════════════

      const usersProcessed = msg.users_processed || 0;

      setDynamicStats((prev) => {
        // Usuarios en compra: solo los procesados en esta sesión
        const newInPurchase = prev.usersInPurchase + usersProcessed;

        return {
          lastJump: typeof msg.last_jump === "number" ? msg.last_jump : prev.lastJump,
          usersInPurchase: newInPurchase,
        };
      });
    }
  }, [lastMessage, isSimMode]);

  // Función auxiliar para formatear segundos en texto legible
  const formatWaitTime = (seconds: number | null) => {
    if (seconds === null) return "Calculando...";
    const mins = Math.floor(seconds / 60);
    if (mins < 1) return "Menos de 1 min";
    return `~${mins} min`;
  };

  return (
    <>
      <div className={styles.statsCard}>
        <p className={styles.statsTitle}>
          {isSimMode ? "⚙️ Métricas de Simulación" : "📊 Información del evento"}
        </p>

        <div className={styles.statsGrid}>
          {isSimMode ? (
            /* ═════════════════════════════════════════════════════════════════════
               UI: SIMULACIÓN AVANZADA
               ═════════════════════════════════════════════════════════════════════ */
            <>
              <div className={styles.statItem}>
                <div className={styles.statValue}>
                  {(simStats.remaining_capacity || 0).toLocaleString()}
                </div>
                <div className={styles.statLabel}>Entradas restantes</div>
              </div>
              <div className={styles.statItem}>
                <div className={`${styles.statValue} ${styles.statValueHighlight}`}>
                  ${simStats.revenue.toLocaleString("es-AR")}
                </div>
                <div className={styles.statLabel}>Recaudación</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statValue} style={{ color: simStats.abandoned_count > 0 ? "#FF5252" : "inherit" }}>
                  {simStats.abandoned_count}
                </div>
                <div className={styles.statLabel}>Abandonaron la fila</div>
              </div>
              <div className={styles.occupancyBar}>
                <div className={styles.occupancyHeader}>
                  <span className={styles.statLabel}>Ocupación del evento</span>
                  <span className={styles.statValue}>
                    {simStats.occupancy_percentage ? simStats.occupancy_percentage.toFixed(1) : "0.0"}%
                  </span>
                </div>
                <div className={styles.occupancyTrack}>
                  <div
                    className={styles.occupancyFill}
                    style={{
                      width: `${Math.min(100, simStats.occupancy_percentage || 0)}%`,
                      backgroundColor:
                        (simStats.occupancy_percentage || 0) > 80
                          ? "var(--color-danger)"
                          : (simStats.occupancy_percentage || 0) > 50
                            ? "var(--color-warning)"
                            : "var(--color-success)",
                    }}
                  />
                </div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statValue}>
                  {simStats.processed_rate || 0}
                </div>
                <div className={styles.statLabel}>Ritmo de venta (u/min)</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statValue}>{simStats.last_jump || 0}</div>
                <div className={styles.statLabel}>Avanzando puestos</div>
              </div>
              <div className={styles.statItem}>
                <div
                  className={styles.statValue}
                  style={{ color: "#4DD0E1" }}
                >
                  {simStats.processed_rate && simStats.processed_rate > 0
                    ? `~${Math.ceil(simStats.remaining_capacity / simStats.processed_rate)} min`
                    : "N/A"}
                </div>
                <div className={styles.statLabel}>Proyección de Sold Out</div>
              </div>
            </>
          ) : (
            /* ═════════════════════════════════════════════════════════════════════
               UI: SIMULACIÓN NORMAL
               ═════════════════════════════════════════════════════════════════════ */
            <>
              <div className={styles.statItem}>
                <div className={styles.statValue}>
                  {stats.queue_length.toLocaleString()}
                </div>
                <div className={styles.statLabel}>Usuarios en total</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statValue}>
                  {formatWaitTime(stats.avg_wait_time_seconds)}
                </div>
                <div className={styles.statLabel}>Espera promedio</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statValue}>2 min</div>
                <div className={styles.statLabel}>Tiempo de compra</div>
              </div>

              <div className={styles.occupancyBar}>
                <div className={styles.occupancyHeader}>
                  <span className={styles.statLabel}>Ocupación del evento</span>
                  <span className={styles.statValue}>
                    {stats.occupancy_percentage ? stats.occupancy_percentage.toFixed(1) : "0.0"}%
                  </span>
                </div>
                <div className={styles.occupancyTrack}>
                  <div
                    className={styles.occupancyFill}
                    style={{
                      width: `${Math.min(100, stats.occupancy_percentage || 0)}%`,
                      backgroundColor:
                        (stats.occupancy_percentage || 0) > 80
                          ? "var(--color-danger)"
                          : (stats.occupancy_percentage || 0) > 50
                            ? "var(--color-warning)"
                            : "var(--color-success)",
                    }}
                  />
                </div>
              </div>

              <div className={styles.statItem}>
                <div className={styles.statValue} style={{ color: "#42A5F5" }}>
                  {dynamicStats.lastJump || stats.last_jump || 0}
                </div>
                <div className={styles.statLabel}>Puestos avanzando</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statValue} style={{ color: "#66BB6A" }}>
                  {dynamicStats.usersInPurchase}
                </div>
                <div className={styles.statLabel}>Usuarios en compra</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statValue} style={{ color: "#FF8A65" }}>
                  {waitingBehind}
                </div>
                <div className={styles.statLabel}>Usuarios detrás tuyo</div>
              </div>
            </>
          )}
        </div>
      </div>

      {isSimMode && (
        <div className={styles.integratedTerminal}>
          <div className={styles.terminalHeader}>
            <span>SYSTEM CONSOLE [MONITORING]</span>
            <span>ID: {eventId || "N/A"}</span>
          </div>
          <div className={styles.logList}>
            {displayLogs.map((log, i) => (
              <div key={i} className={styles.logEntry} style={{ color: getLogColor(log) }}>
                <span className={styles.logTime}>
                  [{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
                </span>
                {log}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
