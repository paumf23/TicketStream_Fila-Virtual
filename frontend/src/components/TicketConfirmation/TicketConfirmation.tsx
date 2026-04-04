"use client";

import React from "react";
import type { TicketDetailResponse } from "@/types";
import { formatPrice, formatDate } from "@/lib/utils";
import styles from "./TicketConfirmation.module.css";

interface TicketConfirmationProps {
  ticket: TicketDetailResponse;
}

export default function TicketConfirmation({ ticket }: TicketConfirmationProps) {
  return (
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
              <span className={styles.detailValue}>
                {formatDate(ticket.event_date)}
              </span>
            </div>
          )}

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Fecha de compra</span>
            <span className={styles.detailValue}>
              {formatDate(ticket.purchased_at)}
            </span>
          </div>

          {ticket.payment_method && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Método de pago</span>
              <span className={styles.detailValue}>
                {ticket.payment_method === "card"
                  ? "Tarjeta de Crédito/Débito"
                  : ticket.payment_method === "wallet"
                  ? "Billetera Virtual"
                  : ticket.payment_method}
                {ticket.payment_provider &&
                  ` (${
                    ticket.payment_provider === "visa"
                      ? "Visa"
                      : ticket.payment_provider === "amex"
                      ? "American Express"
                      : ticket.payment_provider === "mastercard"
                      ? "Master Card"
                      : ticket.payment_provider === "modo"
                      ? "MODO"
                      : ticket.payment_provider === "mercadopago"
                      ? "Mercado Pago"
                      : ticket.payment_provider
                  })`}
              </span>
            </div>
          )}

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Total pagado</span>
            <span className={`${styles.detailValue} ${styles.priceValue}`}>
              {formatPrice(ticket.price_paid, "ARS")}
            </span>
          </div>

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Estado</span>
            <span className={styles.statusBadge}>{ticket.status}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
