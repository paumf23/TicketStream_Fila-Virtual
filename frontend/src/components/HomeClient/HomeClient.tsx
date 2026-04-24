"use client";

import React, { useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import EventCard from "@/components/EventCard/EventCard";
import SimulationDrawer from "@/components/SimulationDrawer/SimulationDrawer";
import type { Event } from "@/types";
import styles from "./HomeClient.module.css";
import Link from "next/link";

interface HomeClientProps {
  initialEvents: Event[];
  category?: string | null;
}

export default function HomeClient({ initialEvents, category }: HomeClientProps) {
  const searchParams = useSearchParams();
  const isSimulationMode = searchParams.get("simulation") === "true";
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Filtrar eventos por categoría (aunque ya vengan filtrados del backend, 
  // esto asegura consistencia en el cliente)
  const filteredEvents = category 
    ? initialEvents.filter(e => e.category === category)
    : initialEvents;

  const handleSimulateClick = (event: Event) => {
    setSelectedEvent(event);
    setIsDrawerOpen(true);
  };

  return (
    <>
      <div className={isDrawerOpen ? "blur" : ""}>
        <section className={styles.hero}>
          <h1 className={styles.title}>
            {isSimulationMode ? "Modo Simulación Activo" : (category ? `${category}` : "Eventos Disponibles")}
          </h1>
          <p className={styles.subtitle}>
            {isSimulationMode 
              ? "Elegí un evento para configurar parámetros de estrés y carga masiva."
              : "Elegí tu evento y entrá a la fila virtual para comprar tus entradas."}
          </p>
          
          {isSimulationMode && (
            <Link href="/" className={styles.exitButton}>
              Salir del Modo Simulación
            </Link>
          )}
        </section>

        {initialEvents.length === 0 ? (
          <div className={styles.emptyContainer}>
            <p className={styles.empty}>
              No hay eventos en este momento.
            </p>
          </div>
        ) : (
          <div className={styles.grid}>
            {filteredEvents.map((event) => (
              <EventCard 
                key={event.event_id} 
                event={event} 
                isSimulationMode={isSimulationMode}
                onSimulate={handleSimulateClick}
              />
            ))}
          </div>
        )}
      </div>

      <SimulationDrawer 
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        selectedEvent={selectedEvent}
      />
    </>
  );
}
