"""End-to-end smoke test against a running server.

Usage: uv run python scripts/smoke.py [http://localhost:8000]

Asserts: session creation, greeting sentences (+ audio or audio_failed), a Claude
reply with suggested topics, show_slides on a pricing ask (needs ANTHROPIC_API_KEY),
and clean interrupt behavior (no stale-gen frames after `interrupted`).
"""

import asyncio
import json
import struct
import sys

import httpx
import websockets

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
WS_BASE = BASE.replace("http", "ws", 1)


def parse(raw):
    if isinstance(raw, bytes):
        gen, seq = struct.unpack(">II", raw[:8])
        return {"type": "_audio_chunk", "gen": gen, "seq": seq, "bytes": len(raw) - 8}
    return json.loads(raw)


async def collect_until(ws, terminal_types, timeout=90):
    events = []
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        ev = parse(raw)
        events.append(ev)
        if ev["type"] in terminal_types:
            return events


async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=15) as http:
        health = (await http.get("/api/health")).json()
        print("health:", health)
        session = (await http.post("/api/sessions")).json()
        print("session:", session["id"], "persona:", session["persona"]["name"])

    async with websockets.connect(f"{WS_BASE}/ws/{session['id']}", max_size=None) as ws:
        # 1. greeting
        events = await collect_until(ws, {"assistant_end"})
        types = [e["type"] for e in events]
        assert "sentence" in types, f"no greeting sentences: {types}"
        assert "suggested_topics" in types, f"no default topics: {types}"
        has_audio = "_audio_chunk" in types
        has_failed = "audio_failed" in types
        assert has_audio or has_failed, "neither audio nor audio_failed in greeting"
        print(f"greeting ok — audio={'yes' if has_audio else 'no (audio_failed fallback)'}")

        # 2. a normal turn
        await ws.send(json.dumps({"type": "user_message", "text": "What do you offer?", "source": "typed"}))
        events = await collect_until(ws, {"assistant_end"})
        sentences = [e for e in events if e["type"] == "sentence"]
        assert sentences, "no reply sentences"
        print(f"reply ok — {len(sentences)} sentences:", sentences[0]["text"][:80])

        # 3. pricing → expect slides (only meaningful with a real LLM key)
        await ws.send(json.dumps({"type": "user_message", "text": "Show me pricing", "source": "topic"}))
        events = await collect_until(ws, {"assistant_end"})
        types = [e["type"] for e in events]
        if "show_slides" in types:
            print("show_slides ok")
        else:
            print("WARN: no show_slides event (expected if ANTHROPIC_API_KEY is unset)")

        # 4. interrupt mid-response
        await ws.send(json.dumps({"type": "user_message", "text": "Tell me a long story about AI workers", "source": "typed"}))
        await asyncio.sleep(2.5)
        await ws.send(json.dumps({"type": "interrupt"}))
        events = await collect_until(ws, {"interrupted"}, timeout=15)
        interrupted_gen = events[-1]["gen"]
        # nothing after `interrupted` may carry an older gen
        await asyncio.sleep(1.0)
        stale = []
        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
                ev = parse(raw)
                if ev.get("gen", interrupted_gen) < interrupted_gen:
                    stale.append(ev)
        except asyncio.TimeoutError:
            pass
        assert not stale, f"stale-gen events after interrupt: {stale[:3]}"
        print("interrupt ok — no stale-gen frames")

        await ws.send(json.dumps({"type": "end_session"}))

    print("\nSMOKE PASSED")


if __name__ == "__main__":
    asyncio.run(main())
