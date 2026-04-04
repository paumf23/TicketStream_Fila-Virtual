"use client";

import React from "react";
import styles from "./TurnNotification.module.css";

interface TurnNotificationProps {
  userName: string;
  turnTTL: number;
  onPurchase: () => void;
  onCancel: () => void;
  onViewEvents: () => void;
}

export default function TurnNotification({
  userName,
  turnTTL,
  onPurchase,
  onCancel,
  onViewEvents,
}: TurnNotificationProps) {
  const isExpired = turnTTL <= 0;
  const minutes = Math.floor(turnTTL / 60);
  const seconds = turnTTL % 60;

  return (
    <>
      {isExpired ? (
        <div className={styles.expiredCard}>
          <span className={styles.turnIcon}>⏰</span>
          <h1 className={styles.expiredTitle}>Se agotó el tiempo</h1>
          <p className={styles.expiredMessage}>
            El tiempo para completar tu compra ha expirado. Volvé a elegir un evento para reiniciar el proceso.
          </p>
          <button className={styles.expiredButton} onClick={onViewEvents}>
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
          <button className={styles.turnButton} onClick={onPurchase}>
            Ir a comprar 🎫
          </button>
          <button className={styles.regretButton} onClick={onCancel}>
            Me arrepentí
          </button>
          <p className={styles.turnTimer}>
            Tiempo restante: {minutes}:{seconds.toString().padStart(2, "0")}
          </p>
        </div>
      )}
    </>
  );
}
