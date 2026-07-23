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
        "title": "EverWorker Overview",
        "description": (
            "5 slides: 'Double your pipeline this quarter' title with customer logos, "
            "the signal-to-booked-meeting flow, live in-market signal intelligence, "
            "'3 to 5x more pipeline, same team', and the Memgraph $2.7M-in-90-days "
            "results story. Show when someone asks what EverWorker is or wants the "
            "big picture."
        ),
        "dir": "slides/overview",
    },
    {
        "_id": "how_it_works_deck",
        "type": "slide_deck",
        "title": "How It Works",
        "description": (
            "4 slides: the autonomous multi-agent system architecture, signal-to-send "
            "with zero human time, the built-in playbook (287% multi-channel "
            "multiplier), and the 5-week go-live timeline with a forward-deployed GTM "
            "engineer. Show when someone asks how it works under the hood or about "
            "implementation."
        ),
        "dir": "slides/how_it_works",
    },
    {
        "_id": "outreach_quality_deck",
        "type": "slide_deck",
        "title": "Outreach Quality",
        "description": (
            "4 slides: account-to-buying-group enrichment, deeply researched personally "
            "written messages, landing in the primary inbox, and 2x replies safely "
            "scaled. Show when someone doubts AI outreach quality, worries about spam, "
            "or asks about personalization."
        ),
        "dir": "slides/outreach_quality",
    },
    {
        "_id": "infrastructure_deck",
        "type": "slide_deck",
        "title": "Sending Infrastructure",
        "description": (
            "2 slides: email infrastructure done for you (domains, warmup, "
            "deliverability) and LinkedIn infrastructure with human-pattern limits. "
            "Show on domain-safety, deliverability, or account-risk concerns."
        ),
        "dir": "slides/infrastructure",
    },
    {
        "_id": "pricing_deck",
        "type": "slide_deck",
        "title": "Pricing & Plans",
        "description": (
            "2 slides: the three packages (Starter $3.5k, Scale $5.5k, Advanced $7k "
            "monthly) with what's included, then the 5-week go-live plan. Show whenever "
            "pricing, cost, or plans come up."
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
