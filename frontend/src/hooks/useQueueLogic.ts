import { useState, useEffect, useCallback } from "react";
import { getQueuePosition, getEventStats } from "@/lib/api";
import { useWebSocket } from "@/lib/websocket";
import type { QueuePositionResponse, EventStats } from "@/types";

export function useQueueLogic(
  eventId: string,
  userId: string | null,
  isSimMode: boolean,
  isMyTurn: boolean,
  onTurnReached: (ttl: number) => void
) {
  const [position, setPosition] = useState<QueuePositionResponse | null>(null);
  const [stats, setStats] = useState<EventStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [waitingBehind, setWaitingBehind] = useState(0);

  const { lastMessage, isConnected } = useWebSocket(eventId);

  const fetchPosition = useCallback(async () => {
    if (!userId || isMyTurn) return;
    try {
      const data = await getQueuePosition(userId, eventId);
      setPosition(data);
      setLoading(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      if (message.includes("no está en la")) {
        onTurnReached(120);
      } else {
        setError(message || "Error al consultar posición");
      }
      setLoading(false);
    }
  }, [userId, eventId, isMyTurn, onTurnReached]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await getEventStats(eventId);
      setStats(data.stats);
    } catch {
      // Ignorar fallos de stats para no bloquear la app
    }
  }, [eventId]);

  // Carga inicial
  useEffect(() => {
    if (userId) {
      fetchPosition();
      fetchStats();
    }
  }, [userId, fetchPosition, fetchStats]);

  // Manejar mensajes de WebSockets (separado del fetch inicial)
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === "your_turn" && lastMessage.user_id === userId) {
      onTurnReached(lastMessage.ttl_seconds);
    }

    if (lastMessage.type === "position_update") {
      if (!isMyTurn) {
        fetchPosition();
      }

      const msg = lastMessage as Record<string, any>;
      setStats((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          processed_count: (prev.processed_count || 0) + (msg.users_processed || 0),
          abandoned_count: (prev.abandoned_count || 0) + (msg.users_abandoned || 0),
          processed_rate: msg.processed_rate !== undefined ? msg.processed_rate : prev.processed_rate,
          throughput: msg.throughput !== undefined ? msg.throughput : prev.throughput,
          tech_logs: msg.tech_logs || prev.tech_logs,
        };
      });

      if (!isSimMode) {
        setWaitingBehind(prev => prev + Math.floor(Math.random() * 4) + 1);
      }
    }
  }, [lastMessage, userId, fetchPosition, isMyTurn, isSimMode, onTurnReached]);

  return {
    position,
    stats,
    error,
    loading,
    waitingBehind,
    isConnected,
    lastMessage
  };
}
