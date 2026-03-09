
# ═══════════════════════════════════════════════════════════════════════════════
# connection_manager.py — Gestor de Conexiones WebSocket
# ═══════════════════════════════════════════════════════════════════════════════


import asyncio
import json
from typing import Optional

from fastapi import WebSocket


class ConnectionManager:
    

    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}
        self.grace_period_seconds: int = 30
        self._grace_period: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, event_id: str) -> None:
        await websocket.accept()
        if event_id not in self._connections:
            self._connections[event_id] = set()
        self._connections[event_id].add(websocket)

    def disconnect(self, websocket: WebSocket, event_id: str) -> None:
     
        if event_id in self._connections:
            self._connections[event_id].discard(websocket)
            
            if not self._connections[event_id]:
                del self._connections[event_id]

    async def send_personal(self, websocket: WebSocket, data: dict) -> None:
        try:
            await websocket.send_json(data)
        except Exception:
            pass

    async def broadcast(self, event_id: str, data: dict) -> None:
        
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
       
        if event_id not in self._connections:
            return 0
        return len(self._connections[event_id])

    def get_total_connections(self) -> int:
        
        return sum(len(conns) for conns in self._connections.values())


manager = ConnectionManager()
