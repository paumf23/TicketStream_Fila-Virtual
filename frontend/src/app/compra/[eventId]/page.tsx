"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getEvent } from "@/lib/api";
import type { Event } from "@/types";
import PurchaseForm from "@/components/PurchaseForm/PurchaseForm";
import styles from "./page.module.css";

export default function PurchasePage() {
  const params = useParams();
  const eventId = params.eventId as string;
  const router = useRouter();

  const [event, setEvent] = useState<Event | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cargar evento y datos guardados
  useEffect(() => {
    async function init() {
      try {
        const data = await getEvent(eventId);
        setEvent(data);
      } catch {
        setError("No se pudo cargar el evento");
      } finally {
        setLoading(false);
      }
    }
    init();

    setUserId(localStorage.getItem("vq_user_id"));
  }, [eventId]);

  if (loading) {
    return <div className={styles.container}><p>Cargando...</p></div>;
  }

  if (error || !event || !userId) {
    return (
      <div className={styles.container}>
        <p className={styles.error}>
          {error || (!userId ? "No se encontró tu identificación. Volvé al evento." : "Evento no encontrado")}
        </p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Completá tu compra</h1>
      <p className={styles.subtitle}>{event.name}</p>

      <PurchaseForm 
        event={event} 
        userId={userId}
        onSuccess={(ticketId) => router.push(`/ticket/${ticketId}`)}
        onCancel={() => router.push("/")}
      />
    </div>
  );
}
