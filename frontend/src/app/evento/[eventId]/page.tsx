"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getEvent, enterQueue, simulateLoad } from "@/lib/api";
import type { Event } from "@/types";
import styles from "./page.module.css";

function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency,
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

export default function EventDetailPage() {
  const params = useParams();
  const eventId = params.eventId as string;
  const router = useRouter();

  const [event, setEvent] = useState<Event | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [entering, setEntering] = useState(false);

  // Estado del formulario
  const [showForm, setShowForm] = useState(false);
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

  async function handleSubmit(e: React.FormEvent) {
    // Prevenir que el formulario recargue la página
    e.preventDefault();

    if (!event || !firstName.trim() || !lastName.trim()) return;
    if (!lettersOnly.test(firstName) || !lettersOnly.test(lastName)) return;

    // Generar un user_id nuevo cada vez que se entra a la fila
    const userId = crypto.randomUUID();
    localStorage.setItem("vq_user_id", userId);

    // Guardar nombre para usarlo después en la compra
    localStorage.setItem("vq_first_name", firstName.trim());
    localStorage.setItem("vq_last_name", lastName.trim());

    setEntering(true);
    try {
      // Simular usuarios en la fila para que el usuario no entre solo.
      // Genera un número aleatorio entre 80 y 150 usuarios ficticios.
      const numSimulated = Math.floor(Math.random() * 71) + 80;
      await simulateLoad(eventId, numSimulated);

      // Ahora sí entra el usuario real a la fila
      await enterQueue({
        user_id: userId,
        event_id: eventId,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });
      router.push(`/cola/${eventId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      // Si ya está en la fila, redirigir a la sala de espera
      if (message.includes("ya está en la")) {
        router.push(`/cola/${eventId}`);
      } else {
        alert(message || "Error al entrar en la fila");
        setEntering(false);
      }
    }
  }

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
      {/* === HERO SECTION === */}
      <section className={styles.hero}>
        {/* Fondo desenfocado */}
        <div 
          className={styles.heroBackground} 
          style={{ backgroundImage: `url("${event.image_url || ""}")` }}
        />
        <div className={styles.heroOverlay} />

        <div className={styles.heroContent}>
          <div className={styles.header}>
            <a href="/" className={styles.backLink}>← Volver</a>
          </div>

          <div className={styles.mainInfo}>
            <div className={styles.imageContainer}>
              {event.image_url ? (
                <img src={event.image_url} alt={event.name} className={styles.mediumImage} />
              ) : (
                <div className={styles.imagePlaceholder}>🎶</div>
              )}
            </div>
            <div className={styles.textContainer}>
              <div className={styles.titleWrapper}>
                <h1 className={styles.title}>{event.name}</h1>
                {event.rating && (
                  <div className={styles.ratingBox}>
                    <span className={styles.ratingValue}>{event.rating}</span>
                    <span className={styles.ratingLabel}>{event.rating_label}</span>
                  </div>
                )}
              </div>
              {event.description && (
                <p className={styles.description}>{event.description}</p>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* === INFO CARDS SECTION === */}
      <div className={styles.container}>
        <div className={styles.statsRow}>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Precio</span>
            <span className={`${styles.statValue} ${styles.priceValue}`}>
              {formatPrice(event.price, event.currency)}
            </span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Calificación</span>
            <div className={styles.ratingValueWrapper}>
              <div className={styles.ratingHeader}>
                <span className={styles.statValue}>{event.rating || "N/A"}</span>
                {event.rating && (
                  <div className={styles.starsContainer}>
                    {[...Array(5)].map((_, i) => (
                      <span 
                        key={i} 
                        className={i < Math.round((event.rating || 0) / 2) ? styles.starFilled : styles.starEmpty}
                      >
                        ★
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {event.rating_label && (
                <span className={styles.ratingSubLabel}>{event.rating_label}</span>
              )}
            </div>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Fecha del Evento</span>
            <span className={styles.statValue}>{formatDate(event.event_date)}</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Venta Hasta</span>
            <span className={styles.statValue}>{formatDate(event.sale_end)}</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statLabel}>Entradas Disponibles</span>
            <span className={styles.statValue}>
              {event.remaining_capacity} / {event.total_capacity}
            </span>
          </div>
        </div>

        {/* === ACTIONS / FORM SECTION === */}
        <div className={styles.actionCenter}>
          {event.status === "active" ? (
            showForm ? (
              <form onSubmit={handleSubmit} className={styles.formCard}>
                <h3 className={styles.formTitle}>Ingresá tus datos</h3>
                <div className={styles.formGrid}>
                  <div className={styles.inputGroup}>
                    <label className={styles.label}>Nombre</label>
                    <input
                      type="text"
                      className={`${styles.input} ${firstNameError ? styles.inputError : ""}`}
                      placeholder="Ej: Juan"
                      value={firstName}
                      onChange={(e) => handleFirstNameChange(e.target.value)}
                      required
                      autoFocus
                    />
                    {firstNameError && <span className={styles.fieldError}>{firstNameError}</span>}
                  </div>
                  <div className={styles.inputGroup}>
                    <label className={styles.label}>Apellido</label>
                    <input
                      type="text"
                      className={`${styles.input} ${lastNameError ? styles.inputError : ""}`}
                      placeholder="Ej: Pérez"
                      value={lastName}
                      onChange={(e) => handleLastNameChange(e.target.value)}
                      required
                    />
                    {lastNameError && <span className={styles.fieldError}>{lastNameError}</span>}
                  </div>
                </div>
                <div className={styles.formButtons}>
                  <button
                    type="button"
                    className={styles.cancelButton}
                    onClick={() => router.push("/")}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className={styles.confirmButton}
                    disabled={entering || !firstName.trim() || !lastName.trim() || !!firstNameError || !!lastNameError}
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
            )
          ) : (
            <div className={styles.soldOutBadge}>
              ❌ Entradas agotadas
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
