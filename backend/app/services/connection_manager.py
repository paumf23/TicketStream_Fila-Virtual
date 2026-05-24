
# ═══════════════════════════════════════════════════════════════════════════════
# Gestor de Conexiones WebSocket en tiempo real
#Registra y desconecta clientes organizándolos por event_id
#Envía mensajes a todos los clientes suscritos a un evento específico
#con send_personal y broadcast
#Identifica y elimina conexiones que dejaron de funcionar
#con get_connection_count y get_total_connections
#Proporciona métricas sobre las conexiones activas
# ═══════════════════════════════════════════════════════════════════════════════


import contextlib

from fastapi import WebSocket


class ConnectionManager:


    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}
        self.grace_period_seconds: int = 30
        self._grace_period: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, event_id: str) -> None:
        """Acepta una nueva conexión WebSocket y la registra para un evento específico."""
        await websocket.accept()
        if event_id not in self._connections:
            self._connections[event_id] = set()
        self._connections[event_id].add(websocket)

    def disconnect(self, websocket: WebSocket, event_id: str) -> None:
        """Elimina una conexión WebSocket del registro de un evento específico."""

        if event_id in self._connections:
            self._connections[event_id].discard(websocket)

            if not self._connections[event_id]:
                del self._connections[event_id]

    async def send_personal(self, websocket: WebSocket, data: dict) -> None:
        """Envía un mensaje JSON a una conexión WebSocket individual."""
        with contextlib.suppress(Exception):
            await websocket.send_json(data)

    async def broadcast(self, event_id: str, data: dict) -> None:
        """Envía un mensaje JSON a todas las conexiones WebSocket suscritas a un evento."""

        if event_id not in self._connections:
            return

        dead_connections = set()
        for websocket in self._connections[event_id]:
            try:
                await websocket.send_json(data)
            except Exception:
                dead_connections.add(websocket)


        for dead in dead_connections:
            self._connections[event_id].discard(dead)

    def get_connection_count(self, event_id: str) -> int:
        """Devuelve la cantidad de conexiones activas para un evento específico."""

        if event_id not in self._connections:
            return 0
        return len(self._connections[event_id])

    def get_total_connections(self) -> int:
        """Devuelve la cantidad total de conexiones activas en todos los eventos."""

        return sum(len(conns) for conns in self._connections.values())


manager = ConnectionManager()
