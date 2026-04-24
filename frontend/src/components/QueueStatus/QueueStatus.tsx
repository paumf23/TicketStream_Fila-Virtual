"use client";

import React from "react";
import type { QueuePositionResponse } from "@/types";
import styles from "./QueueStatus.module.css";

interface QueueStatusProps {
  position: QueuePositionResponse | null;
  error: string | null;
  isConnected: boolean;
  waitingBehind?: number;
}

export default function QueueStatus({ position, error, isConnected, waitingBehind = 0 }: QueueStatusProps) {
  const [initialPosition, setInitialPosition] = React.useState<number | null>(null);

  // Capturamos la primera posición que recibe el usuario como punto de referencia (100%)
  React.useEffect(() => {
    if (position?.position && initialPosition === null) {
      setInitialPosition(position.position);
    }
  }, [position, initialPosition]);

  return (
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
                    initialPosition ? (position.position / initialPosition) * 100 : 100
                  )}%`,
                }}
              />
            </div>
            <span className={styles.progressText}>
              {position.queue_length + waitingBehind} personas en la fila
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
  );
}
