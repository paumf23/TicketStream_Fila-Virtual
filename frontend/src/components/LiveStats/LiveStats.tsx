"use client";

import React from "react";
import type { EventStats } from "@/types";
import styles from "./LiveStats.module.css";

interface LiveStatsProps {
  stats: EventStats;
}

export default function LiveStats({ stats }: LiveStatsProps) {
  return (
    <div className={styles.statsCard}>
      <p className={styles.statsTitle}>📊 Estadísticas en vivo</p>
      <div className={styles.statsGrid}>
        <div className={styles.statItem}>
          <div className={styles.statValue}>{stats.incoming_rate || 0}</div>
          <div className={styles.statLabel}>Ritmo de ingreso (u/min)</div>
        </div>
        <div className={styles.statItem}>
          <div className={`${styles.statValue} ${styles.statValueHighlight}`}>
            ${stats.revenue.toLocaleString("es-AR")}
          </div>
          <div className={styles.statLabel}>Recaudación</div>
        </div>
        <div className={styles.statItem}>
          <div className={styles.statValue} style={{ color: stats.abandoned_count > 0 ? "#FF5252" : "inherit" }}>
            {stats.abandoned_count}
          </div>
          <div className={styles.statLabel}>Abandonaron la fila</div>
        </div>
        <div className={styles.occupancyBar}>
          <div className={styles.occupancyHeader}>
            <span className={styles.statLabel}>Ocupación del evento</span>
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
          <div className={styles.statValue}>
            {stats.throughput || 0}
          </div>
          <div className={styles.statLabel}>Flujo total de salida (u/min)</div>
        </div>
        <div className={styles.statItem}>
          <div className={styles.statValue}>
            {stats.last_jump}
          </div>
          <div className={styles.statLabel}>Avanzando cantidad de puestos</div>
        </div>
        <div className={styles.statItem}>
          <div 
            className={styles.statValue}
            style={{ color: stats.trend <= 0 ? "#4CAF50" : "#FF5252" }}
          >
            {stats.trend > 0 ? `+${stats.trend}` : stats.trend}
          </div>
          <div className={styles.statLabel}>Tendencia de la fila (u/min)</div>
        </div>
      </div>
    </div>
  );
}
