"use client";

import React, { useState, useEffect } from "react";
import styles from "./SimulationHUD.module.css";

interface SimulationHUDProps {
  processedCount: number;
  abandonedCount: number;
  processedRate: number;
  throughput?: number;
  onStop?: () => void;
  onGoHome?: () => void;
}

export default function SimulationHUD({
  processedCount,
  abandonedCount,
  processedRate,
  throughput,
  onStop,
  onGoHome,
}: SimulationHUDProps) {
  const [time, setTime] = useState(0);

  // Reloj de simulación
  useEffect(() => {
    const timer = setInterval(() => setTime((t) => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m
      .toString()
      .padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
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

      <div className={styles.hudActions}>
        <button className={styles.hudButton} onClick={onStop}>
          DETENER SIMULACIÓN
        </button>
        <button className={`${styles.hudButton} ${styles.homeButton}`} onClick={onGoHome}>
          VOLVER A HOME
        </button>
      </div>

      <div className={styles.mainContent}>
        <div className={styles.sideStats}>
          <div className={styles.glassCard}>
            <div className={styles.statLabel}>ATENCIÓN EN TIEMPO REAL</div>
            <div className={styles.statValue}>
              {throughput || processedRate} <span className={styles.statUnit}>u/min</span>
            </div>
          </div>

          <div className={styles.glassCard}>
            <div className={styles.statLabel}>COMPRAS HABILITADAS</div>
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
