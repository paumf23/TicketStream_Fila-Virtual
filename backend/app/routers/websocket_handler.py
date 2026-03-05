
# ═══════════════════════════════════════════════════════════════════════════════
# websocket_handler.py — Endpoint WebSocket para Actualizaciones en Tiempo Real
# ═══════════════════════════════════════════════════════════════════════════════


import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.repositories import redis_repository
from app.services.connection_manager import manager


router = APIRouter()


@router.websocket("/ws/{event_id}")
async def websocket_endpoint(websocket: WebSocket, event_id: str):
    
    await manager.connect(websocket, event_id)

    
    pubsub = await redis_repository.subscribe(event_id)

  
    async def listen_to_redis():
        try:
            async for message in pubsub.listen():
           
                if message["type"] == "message":
                    data = message["data"]
                   
                    try:
                        parsed = json.loads(data)
                    except (json.JSONDecodeError, TypeError):
                        parsed = {"type": "raw", "data": str(data)}

                    await manager.send_personal(websocket, parsed)
        except asyncio.CancelledError:
           
            pass
        except Exception:
            pass

   
    redis_task = asyncio.create_task(listen_to_redis())

    try:
       
        while True:
        
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
       
        redis_task.cancel()
        try:
            await redis_task
        except asyncio.CancelledError:
            pass

        await pubsub.unsubscribe()
        await pubsub.aclose()

        manager.disconnect(websocket, event_id)
