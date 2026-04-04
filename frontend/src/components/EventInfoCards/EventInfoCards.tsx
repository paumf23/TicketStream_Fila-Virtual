"use client";

import React from "react";
import { formatPrice, formatDate } from "@/lib/utils";
import type { Event } from "@/types";
import styles from "./EventInfoCards.module.css";

interface EventInfoCardsProps {
  event: Event;
}


export default function EventInfoCards({ event }: EventInfoCardsProps) {
  return (
    <div className={styles.statsRow}>
      <div className={styles.statCard}>
        <span className={styles.statLabel}>Precio</span>
        <span className={`${styles.statValue} ${styles.priceValue}`}>
          {formatPrice(event.price, event.currency)}
        </span>
      </div>
      <div className={styles.statCard}>
        <span className={styles.statLabel}>Calificación</span>
        <div className={styles.ratingValueWrapper}>
          <div className={styles.ratingHeader}>
            <span className={styles.statValue}>{event.rating || "N/A"}</span>
            {event.rating && (
              <div className={styles.starsContainer}>
                {[...Array(5)].map((_, i) => (
                  <span 
                    key={i} 
                    className={i < Math.round((event.rating || 0) / 2) ? styles.starFilled : styles.starEmpty}
                  >
                    ★
                  </span>
                ))}
              </div>
            )}
          </div>
          {event.rating_label && (
            <span className={styles.ratingSubLabel}>{event.rating_label}</span>
          )}
        </div>
      </div>
      <div className={styles.statCard}>
        <span className={styles.statLabel}>Fecha del Evento</span>
        <span className={styles.statValue}>{formatDate(event.event_date)}</span>
      </div>
      <div className={styles.statCard}>
        <span className={styles.statLabel}>Venta Hasta</span>
        <span className={styles.statValue}>{formatDate(event.sale_end)}</span>
      </div>
      <div className={styles.statCard}>
        <span className={styles.statLabel}>Entradas Disponibles</span>
        <span className={styles.statValue}>
          {event.remaining_capacity} / {event.total_capacity}
        </span>
      </div>
    </div>
  );
}
