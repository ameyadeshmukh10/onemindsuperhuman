import logging

from fastapi import APIRouter, WebSocket

from ..config import settings
from ..orchestrator.agent import SessionRunner
from ..store import get_store

log = logging.getLogger("ws")
router = APIRouter()


@router.websocket("/ws/{session_id}")
async def session_ws(ws: WebSocket, session_id: str):
    store = get_store()
    session = await store.get_session(session_id)
    if session is None:
        await ws.close(code=4404)
        return
    await ws.accept()
    persona = await store.get_persona(session["persona_id"])
    runner = SessionRunner(ws, session, persona, store, settings)
    try:
        await runner.run()
    except Exception:
        log.exception("ws session crashed")
