"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getEvent, purchaseTicket } from "@/lib/api";
import type { Event } from "@/types";
import styles from "./page.module.css";

function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
  }).format(price);
}

export default function PurchasePage() {
  const params = useParams();
  const eventId = params.eventId as string;
  const router = useRouter();

  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Datos del formulario (nombre y apellido se prellenan desde localStorage)
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dni, setDni] = useState("");
  const [email, setEmail] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("credit_card");
  const [quantity, setQuantity] = useState(1);

  // Validation
  const [dniError, setDniError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [firstNameError, setFirstNameError] = useState("");
  const [lastNameError, setLastNameError] = useState("");

  const lettersOnly = /^[a-zA-ZÀ-ÿ\s]*$/;
  const numbersOnly = /^[0-9]*$/;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function handleFirstNameChange(value: string) {
    setFirstName(value);
    setFirstNameError(value && !lettersOnly.test(value) ? "Solo se permiten letras" : "");
  }
  function handleLastNameChange(value: string) {
    setLastName(value);
    setLastNameError(value && !lettersOnly.test(value) ? "Solo se permiten letras" : "");
  }
  function handleDniChange(value: string) {
    setDni(value);
    setDniError(value && !numbersOnly.test(value) ? "Solo se permiten números" : "");
  }
  function handleEmailChange(value: string) {
    setEmail(value);
    setEmailError(value && !emailRegex.test(value) ? "Ingresá un email válido" : "");
  }

  const hasValidationErrors = !!firstNameError || !!lastNameError || !!dniError || !!emailError;

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

    // Prellenar nombre desde localStorage
    setFirstName(localStorage.getItem("vq_first_name") || "");
    setLastName(localStorage.getItem("vq_last_name") || "");
  }, [eventId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!event || hasValidationErrors) return;

    const userId = localStorage.getItem("vq_user_id");
    if (!userId) {
      alert("No se encontró tu identificación. Volvé al evento.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await purchaseTicket({
        user_id: userId,
        event_id: eventId,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        dni: dni.trim(),
        email: email.trim(),
        payment_method: paymentMethod,
        quantity,
      });
      // Redirigir a la confirmación del ticket
      router.push(`/ticket/${result.ticket_id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al comprar");
      setSubmitting(false);
    }
  }

  if (loading) {
    return <div className={styles.container}><p>Cargando...</p></div>;
  }

  if (error || !event) {
    return (
      <div className={styles.container}>
        <p className={styles.error}>{error || "Evento no encontrado"}</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Completá tu compra</h1>
      <p className={styles.subtitle}>{event.name}</p>

      <div className={styles.card}>
        <form onSubmit={handleSubmit} className={styles.form}>

          {/* Datos personales */}
          <div className={styles.section}>
            <p className={styles.sectionTitle}>Datos del comprador</p>
            <div className={styles.row}>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Nombre</label>
                <input
                  type="text"
                  className={`${styles.input} ${firstNameError ? styles.inputError : ""}`}
                  value={firstName}
                  onChange={(e) => handleFirstNameChange(e.target.value)}
                  required
                />
                {firstNameError && <span className={styles.fieldError}>{firstNameError}</span>}
              </div>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Apellido</label>
                <input
                  type="text"
                  className={`${styles.input} ${lastNameError ? styles.inputError : ""}`}
                  value={lastName}
                  onChange={(e) => handleLastNameChange(e.target.value)}
                  required
                />
                {lastNameError && <span className={styles.fieldError}>{lastNameError}</span>}
              </div>
            </div>
            <div className={styles.row}>
              <div className={styles.inputGroup}>
                <label className={styles.label}>DNI</label>
                <input
                  type="text"
                  className={`${styles.input} ${dniError ? styles.inputError : ""}`}
                  placeholder="Ej: 40123456"
                  value={dni}
                  onChange={(e) => handleDniChange(e.target.value)}
                  required
                />
                {dniError && <span className={styles.fieldError}>{dniError}</span>}
              </div>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Email</label>
                <input
                  type="email"
                  className={`${styles.input} ${emailError ? styles.inputError : ""}`}
                  placeholder="Ej: juan@email.com"
                  value={email}
                  onChange={(e) => handleEmailChange(e.target.value)}
                  required
                />
                {emailError && <span className={styles.fieldError}>{emailError}</span>}
              </div>
            </div>
          </div>

          {/* Pago */}
          <div className={styles.section}>
            <p className={styles.sectionTitle}>Pago</p>
            <div className={styles.row}>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Método de pago</label>
                <select
                  className={styles.select}
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                >
                  <option value="credit_card">Tarjeta de crédito</option>
                  <option value="debit_card">Tarjeta de débito</option>
                  <option value="cash">Efectivo</option>
                </select>
              </div>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Cantidad de entradas</label>
                <select
                  className={styles.select}
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                >
                  {[1, 2, 3, 4].map((n) => (
                    <option key={n} value={n}>
                      {n} {n === 1 ? "entrada" : "entradas"}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Resumen */}
          <div className={styles.summary}>
            <span className={styles.summaryLabel}>
              Total ({quantity} {quantity === 1 ? "entrada" : "entradas"})
            </span>
            <span className={styles.summaryPrice}>
              {formatPrice(event.price * quantity, event.currency)}
            </span>
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={submitting || hasValidationErrors}
          >
            {submitting ? "Procesando..." : "💳 Confirmar compra"}
          </button>

          <button
            type="button"
            className={styles.cancelPurchaseButton}
            onClick={() => router.push("/")}
          >
            Cancelar compra
          </button>
        </form>
      </div>
    </div>
  );
}
