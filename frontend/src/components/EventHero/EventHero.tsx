"use client";

/**
 * EventHero.tsx — Cabecera del Evento
 * 
 * Este componente muestra la información principal del evento en la parte superior de la página de detalle.
 * Incluye:
 * - Imagen del evento con efecto de desenfoque en el fondo.
 * - Título del evento y calificación (si está disponible).
 * - Descripción corta del evento.
 * - Enlace para volver a la lista de eventos.
 */

import React from "react";
import Link from "next/link";
import type { Event } from "@/types";
import styles from "./EventHero.module.css";

interface EventHeroProps {
  event: Event;
}

export default function EventHero({ event }: EventHeroProps) {
  return (
    <section className={styles.hero}>
      {/* Fondo desenfocado */}
      <div
        className={styles.heroBackground}
        style={{ backgroundImage: `url("${event.image_url || ""}")` }}
      />
      <div className={styles.heroOverlay} />

      <div className={styles.heroContent}>
        <div className={styles.header}>
          <Link href="/" className={styles.backLink}>← Volver</Link>
        </div>

        <div className={styles.mainInfo}>
          <div className={styles.imageContainer}>
            {event.image_url ? (
              <img src={event.image_url} alt={event.name} className={styles.mediumImage} />
            ) : (
              <div className={styles.imagePlaceholder}>🎶</div>
            )}
          </div>
          <div className={styles.textContainer}>
            <div className={styles.titleWrapper}>
              <h1 className={styles.title}>{event.name}</h1>
              {event.rating && (
                <div className={styles.ratingBox}>
                  <span className={styles.ratingValue}>{event.rating}</span>
                  <span className={styles.ratingLabel}>{event.rating_label}</span>
                </div>
              )}
            </div>
            {event.description && (
              <p className={styles.description}>{event.description}</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
