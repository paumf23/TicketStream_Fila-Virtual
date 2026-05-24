"use client";

/**
 * page.tsx — Página de la Fila Virtual (con Custom Hooks)
 * 
 * Este archivo es el componente principal de la sala de espera. Sus funciones incluyen:
 * 1. Gestionar la conexión WebSocket para recibir actualizaciones de posición y avisos de turno.
 * 2. Visualizar el progreso del usuario mediante el túnel de partículas dinámico.
 * 3. Mostrar estadísticas en tiempo real (LiveStats) y el panel de control de simulación (SimulationHUD).
 * 4. Orquestar la transición hacia la compra de tickets cuando el usuario llega al frente.
 */

import { useState, useCallback, useEffect } from "react";
import { useSearchParams, useParams, useRouter } from "next/navigation";
import ParticleTunnel from "@/components/ParticleTunnel/ParticleTunnel";
import QueueStatus from "@/components/QueueStatus/QueueStatus";
import LiveStats from "@/components/LiveStats/LiveStats";
import TurnNotification from "@/components/TurnNotification/TurnNotification";
import SimulationHUD from "@/components/SimulationHUD/SimulationHUD";
import styles from "./page.module.css";

// Import Custom Hooks
import { useUserIdentity } from "@/hooks/useUserIdentity";
import { useQueueLogic } from "@/hooks/useQueueLogic";
import { useQueueAnimations } from "@/hooks/useQueueAnimations";
import { useTurnTimer } from "@/hooks/useTurnTimer";

export default function QueuePage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const eventId = params.eventId as string;
  const router = useRouter();

  const isSimMode = searchParams.get("sim") === "true";
  const urlUserId = searchParams.get("user_id");

  // --- ESTADO LOCAL COMPARTIDO ---
  const [hyperspace, setHyperspace] = useState(false);
  const [artificialLoading, setArtificialLoading] = useState(true);
  const [isMyTurn, setIsMyTurn] = useState(false);

  // Timer artificial inicial
  useEffect(() => {
    const timer = setTimeout(() => setArtificialLoading(false), 4000);
    return () => clearTimeout(timer);
  }, []);

  // --- CUSTOM HOOKS ---

  // 1. Identidad
  const { userId, userName } = useUserIdentity(isSimMode, urlUserId);

  // 2. Temporizador del Turno
  const { turnTTL, setTurnTTL } = useTurnTimer(isMyTurn, 0);

  // 3. Callback central cuando es tu turno
  const handleTurnReached = useCallback((ttl: number) => {
    setHyperspace(true);
    setTimeout(() => {
      setHyperspace(false);
      setIsMyTurn(true);
      setTurnTTL(ttl);
    }, 2000);
  }, [setTurnTTL]);

  // 4. Lógica de Cola (API + WebSockets)
  const {
    position,
    stats,
    error,
    loading,
    waitingBehind,
    isConnected,
    lastMessage
  } = useQueueLogic(eventId, userId, isSimMode, isMyTurn, handleTurnReached);

  // 5. Animaciones Visuales
  const { burst, speedMultiplier } = useQueueAnimations(position, hyperspace);


  // --- RENDERIZADO ---

  if (loading || artificialLoading) {
    return (
      <>
        <ParticleTunnel speedMultiplier={2.5} burst={false} hyperspace={false} />
        <div className={styles.loadingContainer}>
          <div className={styles.loaderContent}>
            <p className={styles.syncText}>Sincronizando con el servidor...</p>
          </div>
          <div className={styles.spinner}></div>
        </div>
      </>
    );
  }

  if (!userId) {
    return (
      <div className={styles.container}>
        <p className={styles.error}>
          No se encontró tu identificación. Volvé al evento y entrá en la fila nuevamente.
        </p>
      </div>
    );
  }

  if (isMyTurn) {
    return (
      <div className={styles.container}>
        <TurnNotification
          userName={userName}
          turnTTL={turnTTL}
          onPurchase={() => router.push(`/compra/${eventId}`)}
          onCancel={() => router.push("/")}
          onViewEvents={() => router.push("/")}
        />
      </div>
    );
  }

  return (
    <>
      <ParticleTunnel speedMultiplier={speedMultiplier} burst={burst} hyperspace={hyperspace} />
      <div className={`${styles.container} ${isSimMode ? styles.simMode : ""}`}>
        {isSimMode && (
          <SimulationHUD
            processedCount={stats?.processed_count || 0}
            abandonedCount={stats?.abandoned_count || 0}
            processedRate={stats?.processed_rate || 0}
            throughput={stats?.throughput || 0}
            onStop={() => router.push("/?simulation=true")}
            onGoHome={() => router.push("/")}
          />
        )}

        <h1 className={styles.eventName}>
          {isSimMode ? "⚙️ Control de Simulación" : (userName ? `Hola ${userName}` : "Sala de espera")}
        </h1>
        <p className={styles.subtitle}>
          {isSimMode
            ? "La simulación está activa. Los usuarios están siendo procesados según la tasa configurada."
            : "Mantené esta página abierta. Te avisaremos cuando sea tu turno."}
        </p>

        <QueueStatus
          position={position}
          error={error}
          isConnected={isConnected}
          waitingBehind={waitingBehind}
        />

        {stats && (
          <LiveStats
            stats={stats}
            isSimMode={isSimMode}
            lastMessage={lastMessage}
            waitingBehind={waitingBehind}
            eventId={eventId}
          />
        )}
      </div>
    </>
  );
}
