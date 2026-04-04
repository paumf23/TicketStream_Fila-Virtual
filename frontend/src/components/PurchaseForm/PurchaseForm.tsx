"use client";

import React, { useEffect, useState } from "react";
import { purchaseTicket } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import type { Event } from "@/types";
import styles from "./PurchaseForm.module.css";

interface PurchaseFormProps {
  event: Event;
  userId: string;
  onSuccess: (ticketId: string) => void;
  onCancel: () => void;
}


export default function PurchaseForm({
  event,
  userId,
  onSuccess,
  onCancel,
}: PurchaseFormProps) {
  const [submitting, setSubmitting] = useState(false);

  // Datos del formulario
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dni, setDni] = useState("");
  const [email, setEmail] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("card");
  const [paymentProvider, setPaymentProvider] = useState("");
  const [quantity, setQuantity] = useState(1);

  // Validation
  const [dniError, setDniError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [firstNameError, setFirstNameError] = useState("");
  const [lastNameError, setLastNameError] = useState("");
  const [providerError, setProviderError] = useState("");

  const lettersOnly = /^[a-zA-ZÀ-ÿ\s]*$/;
  const numbersOnly = /^[0-9]*$/;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  useEffect(() => {
    // Prellenar nombre desde localStorage
    setFirstName(localStorage.getItem("vq_first_name") || "");
    setLastName(localStorage.getItem("vq_last_name") || "");
  }, []);

  useEffect(() => {
    setPaymentProvider("");
    setProviderError("");
  }, [paymentMethod]);

  function handleFirstNameChange(value: string) {
    setFirstName(value);
    setFirstNameError(
      value && !lettersOnly.test(value) ? "Solo se permiten letras" : ""
    );
  }
  function handleLastNameChange(value: string) {
    setLastName(value);
    setLastNameError(
      value && !lettersOnly.test(value) ? "Solo se permiten letras" : ""
    );
  }
  function handleDniChange(value: string) {
    setDni(value);
    setDniError(
      value && !numbersOnly.test(value) ? "Solo se permiten números" : ""
    );
  }
  function handleEmailChange(value: string) {
    setEmail(value);
    setEmailError(
      value && !emailRegex.test(value) ? "Ingresá un email válido" : ""
    );
  }

  const hasValidationErrors =
    !!firstNameError ||
    !!lastNameError ||
    !!dniError ||
    !!emailError ||
    !!providerError ||
    !paymentProvider;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (hasValidationErrors) return;

    if (!paymentProvider) {
      setProviderError("Por favor seleccioná un medio de pago");
      return;
    }

    setSubmitting(true);
    try {
      const result = await purchaseTicket({
        user_id: userId,
        event_id: event.event_id,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        dni: dni.trim(),
        email: email.trim(),
        payment_method: paymentMethod,
        payment_provider: paymentProvider,
        quantity,
      });
      onSuccess(result.ticket_id);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al comprar");
      setSubmitting(false);
    }
  }

  return (
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
                className={`${styles.input} ${
                  firstNameError ? styles.inputError : ""
                }`}
                value={firstName}
                onChange={(e) => handleFirstNameChange(e.target.value)}
                required
              />
              {firstNameError && (
                <span className={styles.fieldError}>{firstNameError}</span>
              )}
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Apellido</label>
              <input
                type="text"
                className={`${styles.input} ${
                  lastNameError ? styles.inputError : ""
                }`}
                value={lastName}
                onChange={(e) => handleLastNameChange(e.target.value)}
                required
              />
              {lastNameError && (
                <span className={styles.fieldError}>{lastNameError}</span>
              )}
            </div>
          </div>
          <div className={styles.row}>
            <div className={styles.inputGroup}>
              <label className={styles.label}>DNI</label>
              <input
                type="text"
                className={`${styles.input} ${
                  dniError ? styles.inputError : ""
                }`}
                placeholder="Ej: 40123456"
                value={dni}
                onChange={(e) => handleDniChange(e.target.value)}
                required
              />
              {dniError && (
                <span className={styles.fieldError}>{dniError}</span>
              )}
            </div>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Email</label>
              <input
                type="email"
                className={`${styles.input} ${
                  emailError ? styles.inputError : ""
                }`}
                placeholder="Ej: juan@email.com"
                value={email}
                onChange={(e) => handleEmailChange(e.target.value)}
                required
              />
              {emailError && (
                <span className={styles.fieldError}>{emailError}</span>
              )}
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
                <option value="card">Tarjeta de Crédito/Débito</option>
                <option value="wallet">Billetera Virtual</option>
              </select>
            </div>

            {/* Proveedor / Entidad */}
            <div className={styles.inputGroup}>
              <label className={styles.label}>
                {paymentMethod === "card"
                  ? "Seleccioná tu tarjeta"
                  : "Seleccioná tu billetera"}
              </label>
              <select
                className={`${styles.select} ${
                  providerError ? styles.inputError : ""
                }`}
                value={paymentProvider}
                onChange={(e) => {
                  setPaymentProvider(e.target.value);
                  setProviderError("");
                }}
                required
              >
                <option value="" disabled>
                  Elegí una opción
                </option>
                {paymentMethod === "card" ? (
                  <>
                    <option value="visa">Visa</option>
                    <option value="mastercard">Master Card</option>
                    <option value="amex">American Express</option>
                  </>
                ) : (
                  <>
                    <option value="mercadopago">Mercado Pago</option>
                    <option value="modo">MODO</option>
                  </>
                )}
              </select>
              {providerError && (
                <span className={styles.fieldError}>{providerError}</span>
              )}
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
          onClick={onCancel}
        >
          Cancelar compra
        </button>
      </form>
    </div>
  );
}
