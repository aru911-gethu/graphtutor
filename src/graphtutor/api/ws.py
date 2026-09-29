from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["WebSockets"])

# Active connections grouped by task/session id
active_connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/session/{session_id}")
@router.websocket("/research/{session_id}")
async def learning_websocket(websocket: WebSocket, session_id: str):
    """Streams live step-by-step agent thoughts and lesson generation events."""
    await websocket.accept()
    if session_id not in active_connections:
        active_connections[session_id] = set()
    active_connections[session_id].add(websocket)

    try:
        await websocket.send_json({
            "event": "connected",
            "session_id": session_id,
            "message": "Connected to graphtutor learning stream"
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            del active_connections[session_id]


async def broadcast_agent_step(task_id: str, agent_name: str, step_detail: str):
    """Broadcast agent thinking / tool usage events to connected clients."""
    if task_id in active_connections:
        message = {
            "event": "agent_step",
            "task_id": task_id,
            "agent": agent_name,
            "detail": step_detail
        }
        for ws in list(active_connections[task_id]):
            try:
                await ws.send_json(message)
            except Exception:
                pass
