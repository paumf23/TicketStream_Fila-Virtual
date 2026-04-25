"use client";

/**
 * page.tsx — Página de Detalle del Evento
 * 
 * Esta página muestra la información principal del evento y el formulario para unirse a la fila virtual.
 * Sus responsabilidades incluyen:
 * 1. Cargar los datos del evento desde la API.
 * 2. Renderizar el componente de cabecera (EventHero) con la imagen y título del evento.
 * 3. Mostrar las tarjetas informativas (EventInfoCards) con la descripción, fecha, lugar y reglas.
 * 4. Presentar el formulario de ingreso a la fila (EnterQueueForm), que gestiona la lógica de autenticación
 *    y redirección a la sala de espera (cola).
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getEvent } from "@/lib/api";
import type { Event } from "@/types";
import EventHero from "@/components/EventHero/EventHero";
import EventInfoCards from "@/components/EventInfoCards/EventInfoCards";
import EnterQueueForm from "@/components/EnterQueueForm/EnterQueueForm";
import styles from "./page.module.css";

export default function EventDetailPage() {
  const params = useParams();
  const eventId = params.eventId as string;
  const router = useRouter();

  const [event, setEvent] = useState<Event | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    async function loadEvent() {
      try {
        const data = await getEvent(eventId);
        setEvent(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error desconocido");
      } finally {
        setLoading(false);
      }
    }
    loadEvent();
  }, [eventId]);

  if (loading) {
    return <div className={styles.container}><p>Cargando evento...</p></div>;
  }

  if (error || !event) {
    return (
      <div className={styles.container}>
        <p className={styles.error}>{error || "Evento no encontrado"}</p>
      </div>
    );
  }

  return (
    <div className={styles.pageWrapper}>
      <EventHero event={event} />

      <div className={styles.container}>
        <EventInfoCards event={event} />

        <EnterQueueForm
          eventId={eventId}
          eventStatus={event.status}
          onSuccess={() => router.push(`/cola/${eventId}`)}
          onCancel={() => router.push("/")}
        />
      </div>
    </div>
  );
}
