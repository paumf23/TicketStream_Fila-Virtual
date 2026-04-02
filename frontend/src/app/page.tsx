import { getActiveEvents } from "@/lib/api";
import EventCard from "@/components/EventCard/EventCard";
import styles from "./page.module.css";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function HomePage({ 
  searchParams 
}: { 
  searchParams: Promise<{ category?: string }> 
}) {
  const { category } = await searchParams;

  try {
    const data = await getActiveEvents();
    
    // Filtrar por categoría si está presente en la URL (insensible a mayúsculas/minúsculas)
    const filteredEvents = category 
      ? data.events.filter(e => 
          e.category?.toLowerCase() === category.toLowerCase()
        )
      : data.events;

    return (
      <div className={styles.container}>
        <section className={styles.hero}>
          <h1 className={styles.title}>
            {category ? `${category}` : "Eventos Disponibles"}
          </h1>
          <p className={styles.subtitle}>
            Elegí tu evento y entrá a la fila virtual para comprar tus entradas.
          </p>
        </section>

        {filteredEvents.length === 0 ? (
          <div className={styles.emptyContainer}>
            <p className={styles.empty}>
              No hay eventos en la categoría <strong>{category}</strong> en este momento.
            </p>
            <Link href="/" className={styles.resetButton}>Ver todos los eventos</Link>
          </div>
        ) : (
          <div className={styles.grid}>
            {filteredEvents.map((event) => (
              <EventCard key={event.event_id} event={event} />
            ))}
          </div>
        )}

        {/* Footer de Métodos de Pago */}
        {!category && (
          <section className={styles.paymentSection}>
            <div className={styles.paymentCard}>
              <div className={styles.paymentHeader}>
                <span className={styles.paymentIcon}>💳</span>
                <h2 className={styles.paymentTitle}>Métodos de Pago</h2>
              </div>
              <p className={styles.paymentText}>
                Si tenés alguna duda con el pago o querés cancelar tu compra, por favor contactá primero a nuestro equipo de <strong>AYUDA</strong>.
                Evitá iniciar un desconocimiento en tu Banco o Tarjeta: este tipo de gestiones puede generar bloqueos automáticos por actividad sospechosa y afectar futuras compras. Estamos para ayudarte y resolver cualquier inconveniente rápidamente.
              </p>
              <div className={styles.paymentLogos}>
                <img src="/images/payments/visa.png" alt="Visa" className={styles.brandLogo} />
                <img src="/images/payments/Modo.png" alt="MODO" className={styles.brandLogo} />
                <img src="/images/payments/Amex.png" alt="AMEX" className={styles.brandLogo} />
                <img src="/images/payments/mastercard.png" alt="Mastercard" className={styles.brandLogo} />
                <img src="/images/payments/mercadopago.png" alt="Mercado Pago" className={styles.brandLogo} />
              </div>
            </div>
          </section>
        )}
      </div>
    );
  } catch {
    return (
      <div className={styles.container}>
        <section className={styles.hero}>
          <h1 className={styles.title}>Eventos Disponibles</h1>
          <p className={styles.subtitle}>
            Elegí tu evento y entrá a la fila virtual para comprar tus entradas.
          </p>
        </section>
        <p className={styles.error}>
          No se pudieron cargar los eventos. Verificá que el backend esté
          corriendo.
        </p>
      </div>
    );
  }
}
