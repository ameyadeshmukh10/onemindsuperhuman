"""HeyGen LiveAvatar LITE-mode bridge.

Flow (docs.liveavatar.com): POST /v1/sessions/token (X-API-KEY, mode LITE) ->
POST /v1/sessions/start (Bearer session token) -> the browser joins the returned
LiveKit room for lip-synced video while this process connects the returned ws_url
and streams the same ElevenLabs PCM the audio-only mode would have played in the
browser (16-bit 24 kHz, base64, <=1MB per packet). `agent.interrupt` clears
everything buffered avatar-side, mirroring our gen-bump interrupt.

Caption sync: the first packet of each utterance carries event_id "u:<gen>:<seq>".
LiveAvatar echoes event_id on agent.speak_started / agent.speak_ended, which we
surface via callbacks so the client reveals text when the avatar actually speaks.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from typing import Callable

import httpx
import websockets

log = logging.getLogger("liveavatar")

CONNECTED_TIMEOUT = 12.0
KEEPALIVE_INTERVAL = 60.0


def _parse_utterance_id(event_id: str) -> tuple[int, int] | None:
    parts = event_id.split(":") if event_id else []
    if len(parts) == 3 and parts[0] == "u":
        try:
            return int(parts[1]), int(parts[2])
        except ValueError:
            return None
    return None


class LiveAvatarLink:
    def __init__(self, settings):
        self.settings = settings
        self.session_id: str | None = None
        self.session_token: str | None = None
        self.livekit_url: str | None = None
        self.client_token: str | None = None
        self.ws = None
        self.on_speak_started: Callable[[int, int], None] = lambda gen, seq: None
        self.on_speak_ended: Callable[[int, int], None] = lambda gen, seq: None
        self._out_q: asyncio.Queue = asyncio.Queue()
        self._tasks: list[asyncio.Task] = []
        self._connected = asyncio.Event()
        self._closed = False

    @classmethod
    async def create(cls, settings) -> "LiveAvatarLink | None":
        """Create + start a LITE session and connect its command socket.

        Returns None on any failure; callers fall back to audio-only mode."""
        link = cls(settings)
        try:
            await link._start()
            log.info("LiveAvatar session %s started", link.session_id)
            return link
        except Exception as exc:
            log.warning("LiveAvatar unavailable, falling back to audio-only: %s", exc)
            await link.close(reason="UNKNOWN")
            return None

    async def _start(self) -> None:
        base = self.settings.liveavatar_api_base
        async with httpx.AsyncClient(timeout=20.0) as http:
            resp = await http.post(
                f"{base}/v1/sessions/token",
                headers={"X-API-KEY": self.settings.heygen_api_key},
                json={
                    "mode": "LITE",
                    "avatar_id": self.settings.heygen_avatar_id,
                    "is_sandbox": self.settings.heygen_sandbox,
                },
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            self.session_id = data["session_id"]
            self.session_token = data["session_token"]

            resp = await http.post(
                f"{base}/v1/sessions/start",
                headers={"Authorization": f"Bearer {self.session_token}"},
                json={},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            self.livekit_url = data["livekit_url"]
            self.client_token = data["livekit_client_token"]
            ws_url = data.get("ws_url")
            if not ws_url:
                raise RuntimeError("start response had no ws_url")

        self.ws = await websockets.connect(ws_url, max_size=None)
        self._tasks = [
            asyncio.create_task(self._reader()),
            asyncio.create_task(self._sender()),
            asyncio.create_task(self._keepalive()),
        ]
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=CONNECTED_TIMEOUT)
        except asyncio.TimeoutError:
            # Not fatal: some deployments only emit state once media flows.
            log.info("no state=connected within %ss; continuing", CONNECTED_TIMEOUT)

    # ---------- outbound (single sender preserves relay ordering) ----------

    def push_audio(self, pcm: bytes, utterance: tuple[int, int] | None = None) -> None:
        """Queue one PCM chunk. `utterance` tags the first chunk of a sentence."""
        packet: dict = {"type": "agent.speak", "audio": base64.b64encode(pcm).decode()}
        if utterance is not None:
            packet["event_id"] = f"u:{utterance[0]}:{utterance[1]}"
        else:
            packet["event_id"] = uuid.uuid4().hex
        self._out_q.put_nowait(packet)

    def interrupt(self) -> None:
        """Drop any unsent audio, then clear everything buffered avatar-side."""
        while not self._out_q.empty():
            try:
                self._out_q.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._out_q.put_nowait({"type": "agent.interrupt", "event_id": uuid.uuid4().hex})

    async def _sender(self) -> None:
        while True:
            packet = await self._out_q.get()
            if self.ws is None or self._closed:
                continue
            try:
                await self.ws.send(json.dumps(packet))
            except Exception as exc:
                log.warning("send failed, avatar link degraded: %s", exc)
                self._closed = True

    async def _keepalive(self) -> None:
        while True:
            await asyncio.sleep(KEEPALIVE_INTERVAL)
            self._out_q.put_nowait({"type": "session.keep_alive", "event_id": uuid.uuid4().hex})

    # ---------- inbound ----------

    async def _reader(self) -> None:
        try:
            async for raw in self.ws:
                try:
                    ev = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    continue
                etype = ev.get("type")
                if etype == "session.state_updated":
                    state = ev.get("state")
                    if state == "connected":
                        self._connected.set()
                    elif state in ("closing", "closed"):
                        self._closed = True
                elif etype in ("agent.speak_started", "agent.speak_ended"):
                    tagged = _parse_utterance_id(str(ev.get("event_id", "")))
                    if tagged:
                        cb = (
                            self.on_speak_started
                            if etype == "agent.speak_started"
                            else self.on_speak_ended
                        )
                        cb(*tagged)
        except Exception:
            pass

    # ---------- teardown ----------

    async def close(self, reason: str = "USER_CLOSED") -> None:
        """Stop the LiveAvatar session promptly — it bills per minute."""
        self._closed = True
        for task in self._tasks:
            task.cancel()
        self._tasks = []
        if self.ws is not None:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
        if self.session_id:
            try:
                async with httpx.AsyncClient(timeout=10.0) as http:
                    await http.post(
                        f"{self.settings.liveavatar_api_base}/v1/sessions/stop",
                        headers={"X-API-KEY": self.settings.heygen_api_key},
                        json={"session_id": self.session_id, "reason": reason},
                    )
            except Exception as exc:
                log.warning("session stop failed (may idle out on its own): %s", exc)
            self.session_id = None
