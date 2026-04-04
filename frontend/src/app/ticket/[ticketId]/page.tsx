"use client";

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
