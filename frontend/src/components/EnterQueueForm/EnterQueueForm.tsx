"use client";

import React, { useState } from "react";
import { enterQueue, simulateLoad } from "@/lib/api";
import styles from "./EnterQueueForm.module.css";

interface EnterQueueFormProps {
  eventId: string;
  eventStatus: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function EnterQueueForm({
  eventId,
  eventStatus,
  onSuccess,
  onCancel,
}: EnterQueueFormProps) {
  const [showForm, setShowForm] = useState(false);
  const [entering, setEntering] = useState(false);
  
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [firstNameError, setFirstNameError] = useState("");
  const [lastNameError, setLastNameError] = useState("");

  const lettersOnly = /^[a-zA-ZÀ-ÿ\s]*$/;

  function handleFirstNameChange(value: string) {
    setFirstName(value);
    if (value && !lettersOnly.test(value)) {
      setFirstNameError("Solo se permiten letras");
    } else {
      setFirstNameError("");
    }
  }

  function handleLastNameChange(value: string) {
    setLastName(value);
    if (value && !lettersOnly.test(value)) {
      setLastNameError("Solo se permiten letras");
    } else {
      setLastNameError("");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!firstName.trim() || !lastName.trim()) return;
    if (!lettersOnly.test(firstName) || !lettersOnly.test(lastName)) return;

    // Generar un user_id nuevo cada vez que se entra a la fila
    const userId = crypto.randomUUID();
    localStorage.setItem("vq_user_id", userId);

    // Guardar nombre para usarlo después en la compra
    localStorage.setItem("vq_first_name", firstName.trim());
    localStorage.setItem("vq_last_name", lastName.trim());

    setEntering(true);
    try {
      // Simular usuarios en la fila
      const numSimulated = Math.floor(Math.random() * 71) + 80;
      await simulateLoad(eventId, numSimulated);

      // Entrar a la fila real
      await enterQueue({
        user_id: userId,
        event_id: eventId,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });
      onSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      if (message.includes("ya está en la")) {
        onSuccess();
      } else {
        alert(message || "Error al entrar en la fila");
        setEntering(false);
      }
    }
  }

  if (eventStatus !== "active") {
    return (
      <div className={styles.actionCenter}>
        <div className={styles.soldOutBadge}>❌ Entradas agotadas</div>
      </div>
    );
  }

  return (
    <div className={styles.actionCenter}>
      {showForm ? (
        <form onSubmit={handleSubmit} className={styles.formCard}>
          <h3 className={styles.formTitle}>Ingresá tus datos</h3>
          <div className={styles.formGrid}>
            <div className={styles.inputGroup}>
              <label className={styles.label}>Nombre</label>
              <input
                type="text"
                className={`${styles.input} ${
                  firstNameError ? styles.inputError : ""
                }`}
                placeholder="Ej: Juan"
                value={firstName}
                onChange={(e) => handleFirstNameChange(e.target.value)}
                required
                autoFocus
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
                placeholder="Ej: Pérez"
                value={lastName}
                onChange={(e) => handleLastNameChange(e.target.value)}
                required
              />
              {lastNameError && (
                <span className={styles.fieldError}>{lastNameError}</span>
              )}
            </div>
          </div>
          <div className={styles.formButtons}>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={onCancel}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={styles.confirmButton}
              disabled={
                entering ||
                !firstName.trim() ||
                !lastName.trim() ||
                !!firstNameError ||
                !!lastNameError
              }
            >
              {entering ? "Entrando..." : "Confirmar y entrar en fila"}
            </button>
          </div>
        </form>
      ) : (
        <button
          className={styles.floatingEnterButton}
          onClick={() => setShowForm(true)}
        >
          Entrar a la fila
        </button>
      )}
    </div>
  );
}
