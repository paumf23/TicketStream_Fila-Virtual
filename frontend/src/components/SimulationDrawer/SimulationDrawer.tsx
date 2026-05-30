"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { Event } from "@/types";
import { advancedSimulate } from "@/lib/api";
import styles from "./SimulationDrawer.module.css";

interface SimulationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  selectedEvent: Event | null;
}

export default function SimulationDrawer({
  isOpen,
  onClose,
  selectedEvent,
}: SimulationDrawerProps) {
  const router = useRouter();
  const [numUsers, setNumUsers] = useState(100);
  const [includeMe, setIncludeMe] = useState(true);
  const [targetPosition, setTargetPosition] = useState(50);
  const [speed, setSpeed] = useState(60);
  const [abandonRate, setAbandonRate] = useState(0);
  const [eventCapacity, setEventCapacity] = useState(15000);
  const [loading, setLoading] = useState(false);

  // Generar o recuperar ID de usuario persistente
  const [userId, setUserId] = useState<string>("");

  useEffect(() => {
    let id = localStorage.getItem("vq_user_id");
    if (!id) {
      id = "sim-" + Math.random().toString(36).substring(2, 9);
      localStorage.setItem("vq_user_id", id);
      // Se necesitan nombres básicos para que no falle el backend
      localStorage.setItem("vq_first_name", "Usuario");
      localStorage.setItem("vq_last_name", "Simulado");
    }
    setUserId(id);
  }, []);

  if (!selectedEvent) return null;

  const handleLaunch = async () => {
    if (!selectedEvent) return;

    setLoading(true);
    try {
      await advancedSimulate({
        event_id: selectedEvent.event_id,
        num_users: numUsers,
        include_me: includeMe,
        user_id: userId || undefined,
        target_position: includeMe ? targetPosition : undefined,
        processing_speed: speed,
        abandon_rate: abandonRate,
        event_capacity: eventCapacity,
      });

      // Redirigir a la cola en modo simulación
      router.push(`/cola/${selectedEvent.event_id}?sim=true&user_id=${userId}&population=${numUsers}`);
      onClose();
    } catch (error: any) {
      console.error("Error launching simulation:", error);
      const msg = error.message || "Error desconocido";
      alert(`Error al lanzar la simulación: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Overlay para cerrar al hacer clic fuera y blurear fondo */}
      {isOpen && <div className={styles.overlay} onClick={onClose} />}

      <div className={`${styles.drawer} ${isOpen ? styles.drawerOpen : ""}`}>
        <button className={styles.closeButton} onClick={onClose}>
          ✕
        </button>

        <div className={styles.header}>
          <h2 className={styles.title}>Configurá el Sistema</h2>
          <p className={styles.subtitle}>Evento: {selectedEvent.name}</p>
        </div>

        <div className={styles.form}>
          <div className={styles.section}>
            <label className={styles.label}>
              Población Total <span className={styles.value}>{numUsers}</span>
            </label>
            <input
              type="range"
              min="0"
              max="10000"
              step="100"
              value={numUsers}
              onChange={(e) => setNumUsers(parseInt(e.target.value))}
              className={styles.slider}
            />
          </div>

          <div className={styles.section}>
            <div
              className={`${styles.switch} ${includeMe ? styles.switchActive : ""}`}
              onClick={() => setIncludeMe(!includeMe)}
            >
              <span className={styles.switchLabel}>Entrar en la fila (VIP)</span>
              <div className={`${styles.toggle} ${includeMe ? styles.toggleActive : ""}`}>
                <div className={`${styles.dot} ${includeMe ? styles.dotActive : ""}`} />
              </div>
            </div>
          </div>

          {includeMe && (
            <div className={styles.section}>
              <label className={styles.label}>
                Tu Posición Objetivo <span className={styles.value}>#{targetPosition}</span>
              </label>
              <input
                type="range"
                min="1"
                max={Math.max(1, numUsers)}
                value={targetPosition}
                onChange={(e) => setTargetPosition(parseInt(e.target.value))}
                className={styles.slider}
              />
            </div>
          )}

          <div className={styles.section}>
            <label className={styles.label}>
              Velocidad del Motor <span className={styles.value}>{speed} u/min</span>
            </label>
            <input
              type="range"
              min="10"
              max="1000"
              step="10"
              value={speed}
              onChange={(e) => setSpeed(parseInt(e.target.value))}
              className={styles.slider}
            />
          </div>

          <div className={styles.section}>
            <label className={styles.label}>
              Tasa de Abandono <span className={styles.value}>{abandonRate}%</span>
            </label>
            <input
              type="range"
              min="0"
              max="20"
              step="0.5"
              value={abandonRate}
              onChange={(e) => setAbandonRate(parseFloat(e.target.value))}
              className={styles.slider}
            />
          </div>

          <div className={styles.section}>
            <label className={styles.label}>
              Entradas Disponibles <span className={styles.value}>{eventCapacity.toLocaleString()}</span>
            </label>
            <input
              type="range"
              min="10000"
              max="50000"
              step="1000"
              value={eventCapacity}
              onChange={(e) => setEventCapacity(parseInt(e.target.value))}
              className={styles.slider}
            />
          </div>
        </div>

        <div className={styles.actions}>
          <button
            className={styles.launchButton}
            onClick={handleLaunch}
            disabled={loading}
          >
            {loading ? "Procesando Batch..." : "Lanzar Simulación"}
          </button>
        </div>
      </div>
    </>
  );
}
