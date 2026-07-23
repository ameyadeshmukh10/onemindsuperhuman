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
        # Accept before closing so the browser receives the 4404 close code —
        # rejecting the handshake surfaces as a generic failure and the client
        # would keep retrying a session that can never come back.
        await ws.accept()
        await ws.send_json(
            {"type": "error", "code": "session_not_found", "fatal": True, "gen": 0}
        )
        await ws.close(code=4404)
        return
    await ws.accept()
    persona = await store.get_persona(session["persona_id"])
    runner = SessionRunner(ws, session, persona, store, settings)
    try:
        await runner.run()
    except Exception:
        log.exception("ws session crashed")
