"use client";

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
