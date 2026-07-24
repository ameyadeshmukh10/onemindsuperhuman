"""SessionRunner: one instance per WebSocket connection.

Owns the generation counter (interrupt safety), a single outbound writer task
(never write to the WS from two tasks), and at most one in-flight turn task.

Turn flow: Claude token stream -> SentenceChunker -> per sentence: emit `sentence`
event + submit to the TTS relay. Tool_use blocks resolve to UI events that share the
same seq ordering. Continuation requests (tool_result) stay within the same gen.
"""

from __future__ import annotations

import asyncio
import json
import logging
import struct
import uuid

from anthropic import AsyncAnthropic
from fastapi import WebSocket, WebSocketDisconnect

from ..config import Settings
from ..services.liveavatar import LiveAvatarLink
from ..services.tts import TtsRelay
from . import tools as tools_mod
from .chunker import SentenceChunker
from .prompt import build_system_prompt

log = logging.getLogger("agent")

FALLBACK_REPLY = (
    "I'm having trouble reaching my brain right now. Give me a moment and try again, "
    "or use the Book a Meeting button to reach a human."
)


class _Seq:
    """Shared ordering counter for sentences and UI actions within one turn."""

    def __init__(self) -> None:
        self.value = 0

    def next(self) -> int:
        self.value += 1
        return self.value


class SessionRunner:
    def __init__(self, ws: WebSocket, session: dict, persona: dict, store, settings: Settings):
        self.ws = ws
        self.session = session
        self.persona = persona
        self.store = store
        self.settings = settings
        self.gen = 0
        self.turn_task: asyncio.Task | None = None
        self.out_q: asyncio.Queue = asyncio.Queue()
        self.writer_task: asyncio.Task | None = None
        self.claude = AsyncAnthropic() if settings.anthropic_api_key else None
        self.content_items: list[dict] = []
        self._last_user_text: tuple[str, float] | None = None
        self.avatar: LiveAvatarLink | None = None

    # ---------- outbound ----------

    def emit(self, event: dict, gen: int) -> None:
        self.out_q.put_nowait(("json", json.dumps({**event, "gen": gen})))

    def emit_bytes(self, gen: int, seq: int, chunk: bytes) -> None:
        self.out_q.put_nowait(("bytes", struct.pack(">II", gen, seq) + chunk))

    async def _writer(self) -> None:
        while True:
            kind, payload = await self.out_q.get()
            if kind == "json":
                await self.ws.send_text(payload)
            else:
                await self.ws.send_bytes(payload)

    # ---------- lifecycle ----------

    async def run(self) -> None:
        self.writer_task = asyncio.create_task(self._writer())
        self.content_items = await self.store.list_content_items()

        if self.settings.avatar_enabled:
            self.avatar = await LiveAvatarLink.create(self.settings)
            if self.avatar:
                # LiveAvatar echoes our "u:<gen>:<seq>" event ids when the avatar
                # actually starts/finishes an utterance — that drives caption sync.
                self.avatar.on_speak_started = lambda gen, seq: self.emit(
                    {"type": "speak_started", "seq": seq}, gen
                )
                self.avatar.on_speak_ended = lambda gen, seq: self.emit(
                    {"type": "speak_ended", "seq": seq}, gen
                )
                self.emit(
                    {
                        "type": "avatar",
                        "url": self.avatar.livekit_url,
                        "token": self.avatar.client_token,
                    },
                    self.gen,
                )

        history = await self.store.get_messages(self.session["_id"])
        if not history:
            await self._start_turn(self._greeting_turn)
        else:
            self.emit({"type": "state", "status": "idle"}, self.gen)

        try:
            while True:
                raw = await self.ws.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                await self._dispatch(msg)
        except WebSocketDisconnect:
            pass
        finally:
            await self._cancel_turn(emit_event=False)
            if self.avatar:
                await self.avatar.close()  # bills per minute — never leave running
            if self.writer_task:
                self.writer_task.cancel()

    async def _dispatch(self, msg: dict) -> None:
        mtype = msg.get("type")
        if mtype == "ping":
            self.emit({"type": "pong"}, self.gen)
        elif mtype == "user_message":
            text = str(msg.get("text", "")).strip()[:2000]
            source = msg.get("source", "typed")
            if not text or self._is_duplicate(text):
                return
            await self.store.add_event(self.session["_id"], "user_message", {"source": source})
            await self._start_turn(lambda gen: self._assistant_turn(gen, text, source))
        elif mtype == "interrupt":
            # ack unconditionally: `interrupted` means "any prior gen is dead",
            # which is safe (and idempotent) even when no turn was running
            await self._cancel_turn(emit_event=False)
            self.emit({"type": "interrupted"}, self.gen)
            self.emit({"type": "state", "status": "idle"}, self.gen)
            await self.store.add_event(self.session["_id"], "interrupt")
        elif mtype == "analytics":
            await self.store.add_event(
                self.session["_id"], str(msg.get("name", "unknown"))[:64], msg.get("props") or {}
            )
        elif mtype == "end_session":
            await self._cancel_turn(emit_event=False)
            await self.store.set_session_status(self.session["_id"], "ended")
            await self.store.add_event(self.session["_id"], "session_end")
            await self.ws.close()

    def _is_duplicate(self, text: str) -> bool:
        now = asyncio.get_running_loop().time()
        if (
            self._last_user_text
            and self._last_user_text[0] == text
            and now - self._last_user_text[1] < 1.5
        ):
            return True
        self._last_user_text = (text, now)
        return False

    async def _start_turn(self, turn_factory) -> None:
        await self._cancel_turn(emit_event=True)
        gen = self.gen
        self.turn_task = asyncio.create_task(self._run_guarded(turn_factory, gen))

    async def _run_guarded(self, turn_factory, gen: int) -> None:
        try:
            await turn_factory(gen)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("turn failed")
            self.emit(
                {"type": "error", "code": "turn_failed", "message": "turn failed", "fatal": False},
                gen,
            )
            self.emit({"type": "state", "status": "idle"}, gen)

    async def _cancel_turn(self, emit_event: bool) -> None:
        task, self.turn_task = self.turn_task, None
        active = task is not None and not task.done()
        self.gen += 1
        if active and self.avatar:
            self.avatar.interrupt()  # clears queued + avatar-buffered speech
        if active:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
            if emit_event:
                self.emit({"type": "interrupted"}, self.gen)
                await self.store.add_event(self.session["_id"], "interrupt")

    # ---------- turns ----------

    def _new_relay(self, gen: int) -> TtsRelay:
        if self.avatar:
            # Avatar mode: ordered PCM goes to LiveAvatar (which lip-syncs and
            # carries the audio in its WebRTC stream) instead of the browser.
            # audio_failed still reaches the client so text reveals without audio.
            pending_first: set[int] = set()

            def emit_json(event: dict) -> None:
                if event["type"] == "audio_start":
                    pending_first.add(event["seq"])
                elif event["type"] == "audio_failed":
                    self.emit(event, gen)

            def emit_bytes(seq: int, chunk: bytes) -> None:
                tag = (gen, seq) if seq in pending_first else None
                pending_first.discard(seq)
                self.avatar.push_audio(chunk, utterance=tag)

            return TtsRelay(
                self.settings,
                gen,
                emit_json,
                emit_bytes,
                output_format=self.settings.avatar_tts_output_format,
                sample_rate=self.settings.avatar_tts_sample_rate,
            )
        return TtsRelay(
            self.settings,
            gen,
            lambda event: self.emit(event, gen),
            lambda seq, chunk: self.emit_bytes(gen, seq, chunk),
        )

    async def _greeting_turn(self, gen: int) -> None:
        """Scripted opener: straight to TTS, no LLM call — instant and cheap."""
        relay = self._new_relay(gen)
        seq = _Seq()
        sentences: list[str] = []
        try:
            self.emit({"type": "state", "status": "speaking"}, gen)
            self.emit({"type": "assistant_start", "message_id": uuid.uuid4().hex}, gen)
            chunker = SentenceChunker()
            parts = chunker.feed(self.persona["greeting"] + " ")
            tail = chunker.flush()
            if tail:
                parts.append(tail)
            for part in parts:
                n = seq.next()
                sentences.append(part)
                self.emit({"type": "sentence", "seq": n, "text": part}, gen)
                relay.submit(n, part)
            self.emit(
                {
                    "type": "suggested_topics",
                    "seq": seq.next(),
                    "topics": self.persona["default_topics"],
                },
                gen,
            )
            await relay.close()
            self.emit({"type": "assistant_end", "stop_reason": "end_turn"}, gen)
            self.emit({"type": "state", "status": "idle"}, gen)
            await self.store.add_message(
                self.session["_id"],
                {"role": "assistant", "text": " ".join(sentences), "source": "greeting"},
            )
        except asyncio.CancelledError:
            relay.abort()
            await self._persist_partial(sentences)
            raise

    async def _assistant_turn(self, gen: int, user_text: str, source: str) -> None:
        await self.store.add_message(
            self.session["_id"], {"role": "user", "text": user_text, "source": source}
        )
        self.emit({"type": "state", "status": "thinking"}, gen)

        relay = self._new_relay(gen)
        seq = _Seq()
        sentences: list[str] = []
        started = False

        def dispatch_sentence(text: str) -> None:
            nonlocal started
            if not started:
                self.emit({"type": "assistant_start", "message_id": uuid.uuid4().hex}, gen)
                self.emit({"type": "state", "status": "speaking"}, gen)
                started = True
            n = seq.next()
            sentences.append(text)
            self.emit({"type": "sentence", "seq": n, "text": text}, gen)
            relay.submit(n, text)

        try:
            if self.claude is None:
                dispatch_sentence(FALLBACK_REPLY)
                stop_reason = "end_turn"
            else:
                stop_reason = await self._claude_loop(gen, user_text, dispatch_sentence, seq)
            await relay.close()
            self.emit({"type": "assistant_end", "stop_reason": stop_reason or "end_turn"}, gen)
            self.emit({"type": "state", "status": "idle"}, gen)
            await self.store.add_message(
                self.session["_id"],
                {"role": "assistant", "text": " ".join(sentences), "source": "llm"},
            )
        except asyncio.CancelledError:
            relay.abort()
            await self._persist_partial(sentences)
            raise

    async def _claude_loop(self, gen: int, user_text: str, dispatch_sentence, seq: _Seq) -> str:
        """Stream from Claude, handling tool-use continuations within the same gen."""
        history = await self._build_history()
        messages = history + [{"role": "user", "content": user_text}]
        system = build_system_prompt(self.persona, self.content_items)
        stop_reason = "end_turn"

        for _round in range(6):  # hard cap on tool-use continuations
            chunker = SentenceChunker()
            async with self.claude.messages.stream(
                model=self.settings.anthropic_model,
                max_tokens=self.settings.anthropic_max_tokens,
                system=system,
                messages=messages,
                tools=tools_mod.TOOL_DEFINITIONS,
                thinking={"type": "disabled"},
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta" and event.delta.type == "text_delta":
                        for sentence in chunker.feed(event.delta.text):
                            dispatch_sentence(sentence)
                    elif event.type == "content_block_stop":
                        # flush before a possible tool block so slides never precede
                        # the sentence that introduces them
                        tail = chunker.flush()
                        if tail:
                            dispatch_sentence(tail)
                final = await stream.get_final_message()

            stop_reason = final.stop_reason or "end_turn"
            if stop_reason != "tool_use":
                break

            messages.append({"role": "assistant", "content": final.content})
            tool_results = []
            for block in final.content:
                if block.type != "tool_use":
                    continue
                ui_event, result = tools_mod.execute(block.name, block.input, self.content_items)
                if ui_event:
                    self.emit({**ui_event, "seq": seq.next()}, gen)
                    await self.store.add_event(
                        self.session["_id"], ui_event["type"], {"tool": block.name}
                    )
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
            messages.append({"role": "user", "content": tool_results})
        return stop_reason

    async def _build_history(self) -> list[dict]:
        docs = await self.store.get_messages(self.session["_id"])
        messages: list[dict] = []
        for doc in docs[-30:]:
            text = doc.get("text", "")
            if not text:
                continue
            if doc.get("interrupted"):
                text += " [user interrupted]"
            messages.append({"role": doc["role"], "content": text})
        return messages

    async def _persist_partial(self, sentences: list[str]) -> None:
        if sentences:
            await self.store.add_message(
                self.session["_id"],
                {"role": "assistant", "text": " ".join(sentences), "interrupted": True},
            )
