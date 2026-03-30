// ══════════════════════════════════════════════════════════════
// lib/websocket.ts — Hook de WebSocket para actualizaciones en tiempo real
// ══════════════════════════════════════════════════════════════
// Este hook se usa en la página de la sala de espera (cola).
// Se conecta al WebSocket del backend y recibe mensajes del worker
// cuando avanza la cola o cuando le llega el turno al usuario.
// ══════════════════════════════════════════════════════════════

"use client";


import { useEffect, useRef, useState, useCallback } from "react";
import type { WsMessage } from "@/types";

// URL base del WebSocket del backend.
// Usa "ws://" porque es el protocolo de WebSocket.
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";


export function useWebSocket(eventId: string) {
  // Estado: el último mensaje recibido del WebSocket
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);

  // Estado: si la conexión está activa o no
  const [isConnected, setIsConnected] = useState(false);

  // Referencia al objeto WebSocket (persiste entre renders sin causar re-renders)
  const wsRef = useRef<WebSocket | null>(null);

  // Función para conectar (o reconectar) al WebSocket
  const connect = useCallback(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/${eventId}`);

    // Cuando la conexión se abre exitosamente
    ws.onopen = () => setIsConnected(true);

    // Cuando llega un mensaje del servidor (worker)
    ws.onmessage = (event) => {
      const data: WsMessage = JSON.parse(event.data);
      setLastMessage(data);
    };

    // Cuando la conexión se cierra (por error o desconexión)
    ws.onclose = () => {
      setIsConnected(false);
      // Reintentar la conexión después de 3 segundos
      setTimeout(connect, 3000);
    };

    // Si hay un error, cerrar la conexión (onclose se encarga de reconectar)
    ws.onerror = () => ws.close();

    wsRef.current = ws;
  }, [eventId]);

  // useEffect: cuando el componente aparece en pantalla, conectar.
  // Cuando desaparece (el usuario navega a otra página), desconectar.
  useEffect(() => {
    connect();

    // Función de "limpieza": se ejecuta cuando el componente se desmonta
    return () => wsRef.current?.close();
  }, [connect]);

  return { lastMessage, isConnected };
}
