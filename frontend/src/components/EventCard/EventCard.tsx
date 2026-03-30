import Link from "next/link";
import type { Event } from "@/types";
import styles from "./EventCard.module.css";

// Función auxiliar para formatear el precio (ej: 50000 → "$50.000")
function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: currency,
    minimumFractionDigits: 0,
  }).format(price);
}

// Función auxiliar para formatear la fecha (ej: "2026-12-31" → "31 de dic. de 2026")
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("es-AR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

// Props: los datos que este componente necesita para funcionar.
// Recibe un objeto "event" del tipo Event (definido en types/index.ts).
interface EventCardProps {
  event: Event;
}

export default function EventCard({ event }: EventCardProps) {
  return (
    <Link href={`/evento/${event.event_id}`} className={styles.card}>
      {/* Imagen del evento o un placeholder con gradiente */}
      <div className={styles.imageContainer}>
        {event.image_url ? (
          <>
            <div 
              className={styles.imageBlur} 
              style={{ backgroundImage: `url("${event.image_url}")` }}
            />
            <img
              src={event.image_url}
              alt={event.name}
              className={styles.image}
            />
          </>
        ) : (
          <div className={styles.imagePlaceholder}>🎶</div>
        )}
      </div>

      <div className={styles.content}>
        <div className={styles.ratingInfo}>
          <span className={styles.ratingValue}>{event.rating || "N/A"}</span>
          {event.rating && (
            <div className={styles.stars}>
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

        {event.description && (
          <p className={styles.description}>{event.description}</p>
        )}

        <div className={styles.details}>
          <span className={styles.price}>
            {formatPrice(event.price, event.currency)}
          </span>
          <span className={styles.date}>
            {formatDate(event.event_date)}
          </span>
        </div>

        <div className={styles.footer}>
          <span className={styles.capacity}>
            {event.remaining_capacity} / {event.total_capacity} disponibles
          </span>
          <span
            className={`${styles.status} ${
              event.status === "active"
                ? styles.statusActive
                : event.status === "draft"
                ? styles.statusUpcoming
                : styles.statusSoldOut
            }`}
          >
            {event.status === "active"
              ? "Entradas disponibles"
              : event.status === "draft"
              ? "Próximamente"
              : "Agotado"}
          </span>
        </div>
      </div>
    </Link>
  );
}
