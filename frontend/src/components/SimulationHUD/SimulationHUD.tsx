"use client";

import React, { useState, useEffect } from "react";
import styles from "./SimulationHUD.module.css";

interface SimulationHUDProps {
  processedCount: number;
  abandonedCount: number;
  processedRate: number;
  techLogs?: string[];
}

export default function SimulationHUD({
  processedCount,
  abandonedCount,
  processedRate,
  techLogs = [],
}: SimulationHUDProps) {
  const [time, setTime] = useState(0);
  const [displayLogs, setDisplayLogs] = useState<string[]>([]);

  // Reloj de simulación
  useEffect(() => {
    const timer = setInterval(() => setTime((t) => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  // Actualizar logs cuando llegan nuevos logs técnicos del backend
  useEffect(() => {
    if (techLogs && techLogs.length > 0) {
      setDisplayLogs((prev) => {
        // Combinar logs nuevos con los viejos, manteniendo un límite de 8 para legibilidad
        const combined = [...prev, ...techLogs];
        return combined.slice(-8);
      });
    }
  }, [techLogs]);

  // Logs iniciales de bienvenida
  useEffect(() => {
    const initial = [
      "[WEBSOCKET] Conexión en tiempo real establecida",
      "[SISTEMA] Motor de simulación en espera...",
      "[REDIS] Caché de cola vinculada",
    ];
    setDisplayLogs(initial);
  }, []);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m
      .toString()
      .padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const getLogColor = (log: string) => {
    if (log.includes("[WEBSOCKET]")) return "#4CAF50"; // Verde
    if (log.includes("[REDIS]")) return "#2196F3"; // Azul
    if (log.includes("[WORKER]")) return "#E040FB"; // Violeta
    if (log.includes("[SISTEMA]")) return "#FFD700"; // Dorado
    return "rgba(255, 255, 255, 0.7)";
  };

  return (
    <div className={styles.hud}>
      <div className={styles.scanlines} />
      
      <div className={styles.topBar}>
        <div className={styles.simStatus}>
          <span className={styles.pulseDot}></span>
          SIMULATION MODE: ACTIVE
        </div>
        <div className={styles.simTime}>
          SIM TIME: {formatTime(time)}
        </div>
      </div>

      <div className={styles.mainContent}>
        <div className={styles.terminal}>
          <div className={styles.terminalHeader}>
            SYSTEM CONSOLE [v1.2.0] — {window.location.pathname.split("/").pop()}
          </div>
          <div className={styles.logList}>
            {displayLogs.map((log, i) => (
              <div 
                key={i} 
                className={styles.logEntry} 
                style={{ 
                  color: getLogColor(log),
                  fontFamily: "'Roboto Mono', monospace",
                  fontSize: '11px',
                  lineHeight: '1.4',
                  marginBottom: '4px'
                }}
              >
                <span style={{ opacity: 0.5, marginRight: '8px' }}>
                  [{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
                </span>
                <span>{log}</span>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.sideStats}>
          <div className={styles.glassCard}>
            <div className={styles.statLabel}>Procesamiento Real</div>
            <div className={styles.statValue}>
              {processedRate} <span className={styles.statUnit}>u/min</span>
            </div>
          </div>

          <div className={styles.glassCard}>
            <div className={styles.statLabel}>Accedieron a la compra</div>
            <div className={styles.statValue}>{processedCount}</div>
          </div>

          <div className={styles.glassCard}>
            <div className={styles.statLabel}>Tasa de Éxito del Procesamiento</div>
            <div className={styles.statValue} style={{ color: "#4CAF50" }}>
              {processedCount + abandonedCount > 0 
                ? ((processedCount / (processedCount + abandonedCount)) * 100).toFixed(1) 
                : "100"}
              <span className={styles.statUnit}>%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
