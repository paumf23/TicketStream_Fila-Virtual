"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getTicketDetail } from "@/lib/api";
import type { TicketDetailResponse } from "@/types";
import styles from "./page.module.css";

function formatPrice(price: number): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 0,
  }).format(price);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("es-AR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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
      <div className={styles.successIcon}>✅</div>
      <h1 className={styles.title}>¡Compra exitosa!</h1>
      <p className={styles.subtitle}>Tu entrada fue confirmada</p>

      <div className={styles.card}>
        <div className={styles.ticketHeader}>
          <span className={styles.eventName}>{ticket.event_name}</span>
          <span className={styles.ticketCode}>{ticket.ticket_code}</span>
        </div>

        <div className={styles.details}>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Comprador</span>
            <span className={styles.detailValue}>{ticket.buyer_name}</span>
          </div>

          {ticket.event_date && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Fecha del evento</span>
              <span className={styles.detailValue}>{formatDate(ticket.event_date)}</span>
            </div>
          )}

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Fecha de compra</span>
            <span className={styles.detailValue}>{formatDate(ticket.purchased_at)}</span>
          </div>

          {ticket.payment_method && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Método de pago</span>
              <span className={styles.detailValue}>
                {ticket.payment_method === "card" ? "Tarjeta de Crédito/Débito" :
                 ticket.payment_method === "wallet" ? "Billetera Virtual" :
                 ticket.payment_method}
                {ticket.payment_provider && ` (${
                  ticket.payment_provider === "visa" ? "Visa" :
                  ticket.payment_provider === "amex" ? "American Express" :
                  ticket.payment_provider === "mastercard" ? "Master Card" :
                  ticket.payment_provider === "modo" ? "MODO" :
                  ticket.payment_provider === "mercadopago" ? "Mercado Pago" :
                  ticket.payment_provider
                })`}
              </span>
            </div>
          )}

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Total pagado</span>
            <span className={`${styles.detailValue} ${styles.priceValue}`}>
              {formatPrice(ticket.price_paid)}
            </span>
          </div>

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Estado</span>
            <span className={styles.statusBadge}>{ticket.status}</span>
          </div>
        </div>
      </div>

      <div className={styles.actions}>
        <Link href="/" className={styles.homeButton}>
          Volver a eventos
        </Link>
      </div>
    </div>
    </>
  );
}

// ── Confetti Canvas Component ──
interface ConfettiPiece {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  rotation: number;
  rotationSpeed: number;
  color: string;
  opacity: number;
  gravity: number;
}

const CONFETTI_COLORS = [
  "#00B894", // exact --color-success
  "#00D9A3", // lighter variant
  "#009B7D", // darker variant
  "#55EFC4", // bright variant
  "#00CEC9", // secondary accent
];

function ConfettiCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const piecesRef = useRef<ConfettiPiece[]>([]);
  const animRef = useRef<number>(0);
  const burstCountRef = useRef(0);

  const createCornerBurst = useCallback((originX: number, originY: number, targetX: number, targetY: number) => {
    const newPieces: ConfettiPiece[] = [];
    // Direction from origin toward target (center)
    const baseAngle = Math.atan2(targetY - originY, targetX - originX);

    for (let i = 0; i < 60; i++) {
      // Spread angle: ±45° around the direction toward center
      const angle = baseAngle + (Math.random() - 0.5) * (Math.PI / 2);
      const speed = 6 + Math.random() * 10;
      newPieces.push({
        x: originX + (Math.random() - 0.5) * 40,
        y: originY + (Math.random() - 0.5) * 20,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: 8 + Math.random() * 6,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 15,
        color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
        opacity: 1,
        gravity: 0.08 + Math.random() * 0.06,
      });
    }
    piecesRef.current.push(...newPieces);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    // The "center" of the visible page (where the card is)
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // Two corners: bottom-left and bottom-right
    const leftX = 0;
    const rightX = canvas.width;
    const bottomY = canvas.height;

    // Fire both groups simultaneously
    function fireBurst() {
      createCornerBurst(leftX, bottomY, centerX, centerY);
      createCornerBurst(rightX, bottomY, centerX, centerY);
    }

    fireBurst();
    burstCountRef.current = 1;

    const burstInterval = setInterval(() => {
      burstCountRef.current += 1;
      fireBurst();
      if (burstCountRef.current >= 3) {
        clearInterval(burstInterval);
      }
    }, 1500);

    function animate() {
      const ctx = canvas!.getContext("2d");
      if (!ctx) return;

      ctx.clearRect(0, 0, canvas!.width, canvas!.height);

      const pieces = piecesRef.current;
      for (let i = pieces.length - 1; i >= 0; i--) {
        const p = pieces[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += p.gravity;
        p.vx *= 0.985;
        p.rotation += p.rotationSpeed;
        p.opacity -= 0.004;

        if (p.opacity <= 0 || p.y > canvas!.height + 30 || p.x < -30 || p.x > canvas!.width + 30) {
          pieces.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = p.opacity;
        ctx.fillStyle = p.color;
        // Bigger rectangular confetti pieces
        ctx.fillRect(-p.size / 2, -p.size / 3, p.size, p.size * 0.6);
        ctx.restore();
      }

      animRef.current = requestAnimationFrame(animate);
    }

    animRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animRef.current);
      clearInterval(burstInterval);
      window.removeEventListener("resize", handleResize);
    };
  }, [createCornerBurst]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        pointerEvents: "none",
        zIndex: 100,
      }}
    />
  );
}
