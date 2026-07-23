"""Persona and content-item definitions, seeded idempotently on startup.

To add content: drop assets under backend/content/ and register them here.
Video items whose file is missing are skipped (add backend/content/videos/demo.mp4
to enable the play_video capability).
"""

from .config import CONTENT_DIR, settings

PERSONA = {
    "_id": "evie",
    "name": "Evie",
    "tagline": "Your Everworker Guide",
    "description": (
        "Evie is our AI-powered guide, here to show you how EverWorker's autonomous AI "
        "workers research accounts, write personalized outreach, and book meetings — so "
        "your team generates more pipeline, on autopilot. Whether you're exploring or "
        "ready to put AI workers on your funnel, Evie has the answers."
    ),
    "voice_id": settings.elevenlabs_voice_id,
    "image_path": None,  # set automatically at seed time if backend/content/persona.* exists
    "greeting": (
        "Hi there, I'm Evie, EverWorker's AI guide. I can show you how autonomous AI "
        "workers research accounts, write personalized outreach, and book meetings for "
        "your team — and help you book time with our team if you'd like to go deeper. "
        "What brought you here today?"
    ),
    "default_topics": ["What is EverWorker?", "How does outbound work?", "Pricing"],
    "mic_disclaimer": (
        "If you use the microphone, your audio is processed by your browser's speech "
        "service and this demo's AI providers."
    ),
}

SLIDE_DECKS = [
    {
        "_id": "overview_deck",
        "type": "slide_deck",
        "title": "Everworker Overview",
        "description": (
            "3 slides introducing Everworker: what AI workers are, how they plug into "
            "existing tools, and example roles they can take on. Show when someone asks "
            "what Everworker is or how it works."
        ),
        "dir": "slides/overview",
    },
    {
        "_id": "pricing_deck",
        "type": "slide_deck",
        "title": "Pricing & Plans",
        "description": (
            "3 slides covering pricing tiers and what's included. Show when pricing, "
            "cost, or plans come up."
        ),
        "dir": "slides/pricing",
    },
]

VIDEOS = [
    {
        "_id": "demo_clip",
        "type": "video",
        "title": "EverWorker demo reel",
        "description": (
            "A thirty-one second EverWorker demo reel. Play when someone asks to see "
            "EverWorker in action, asks for a demo, or wants the quick version."
        ),
        "file": "videos/demo.mp4",
    },
]


async def seed(store) -> None:
    persona = dict(PERSONA)
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (CONTENT_DIR / f"persona.{ext}").exists():
            persona["image_path"] = f"/content/persona.{ext}"
            break
    await store.upsert_persona(persona)

    for deck in SLIDE_DECKS:
        deck_dir = CONTENT_DIR / deck["dir"]
        slides = sorted(p.name for p in deck_dir.glob("*.png")) if deck_dir.exists() else []
        if not slides:
            continue
        await store.upsert_content_item(
            {
                "_id": deck["_id"],
                "type": "slide_deck",
                "title": deck["title"],
                "description": deck["description"],
                "assets": [f"/content/{deck['dir']}/{name}" for name in slides],
            }
        )

    for video in VIDEOS:
        if not (CONTENT_DIR / video["file"]).exists():
            continue
        await store.upsert_content_item(
            {
                "_id": video["_id"],
                "type": "video",
                "title": video["title"],
                "description": video["description"],
                "assets": [f"/content/{video['file']}"],
            }
        )
