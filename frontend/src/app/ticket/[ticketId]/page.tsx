"use client";

/**
 * page.tsx — Página de Confirmación de Ticket
 * 
 * Esta página se muestra después de que el usuario ha comprado un ticket y ha llegado al frente de la fila.
 * Sus responsabilidades incluyen:
 * 1. Cargar los detalles del ticket utilizando el ID proporcionado en la URL.
 * 2. Renderizar el componente TicketConfirmation para mostrar la información del ticket y un mensaje de éxito.
 * 3. Activar una animación de confeti (ConfettiCanvas) para celebrar la compra.
 * 4. Proporcionar un enlace para volver a la página principal de eventos.
 */

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getTicketDetail } from "@/lib/api";
import type { TicketDetailResponse } from "@/types";
import ConfettiCanvas from "@/components/common/ConfettiCanvas/ConfettiCanvas";
import TicketConfirmation from "@/components/TicketConfirmation/TicketConfirmation";
import styles from "./page.module.css";

export default function TicketPage() {
  const params = useParams();
  const ticketId = params.ticketId as string;

  const [ticket, setTicket] = useState<TicketDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadTicket() {
      try {
        const data = await getTicketDetail(ticketId);
        setTicket(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al cargar el ticket");
      } finally {
        setLoading(false);
      }
    }
    loadTicket();
  }, [ticketId]);

  if (loading) {
    return <div className={styles.container}><p className={styles.loading}>Cargando ticket...</p></div>;
  }

  if (error || !ticket) {
    return (
      <div className={styles.container}>
        <p className={styles.error}>{error || "Ticket no encontrado"}</p>
      </div>
    );
  }

  return (
    <>
      <ConfettiCanvas />
      <div className={styles.container}>
        <TicketConfirmation ticket={ticket} />

        <div className={styles.actions}>
          <Link href="/" className={styles.homeButton}>
            Volver a eventos
          </Link>
        </div>
      </div>
    </>
  );
}
