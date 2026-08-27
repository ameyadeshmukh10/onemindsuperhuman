"""Persona and content-item definitions, seeded idempotently on startup.

To add content: drop assets under backend/content/ and register them here.
Video items whose file is missing are skipped (add backend/content/videos/demo.mp4
to enable the play_video capability).
"""

from .config import CONTENT_DIR, settings

PERSONA = {
    "_id": "evie",
    "name": "Evie",
    "company": "EverWorker",
    "website": "everworker.ai",
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
        "presenter_notes": [
            "EverWorker is a multi-agent AI system that generates pipeline on autopilot.",
            "It handles both inbound and outbound, integrates with your CRM, researches "
            "accounts and leads, writes and sends email plus LinkedIn sequences, and "
            "books meetings directly on your reps' calendars.",
            "Built-in agentic signal intelligence continuously scans your ICP to surface "
            "in-market accounts and begins outreach before they go cold.",
            "As it works it automatically enriches the buying group and reaches out to "
            "them simultaneously with personalized messaging — it handles the operations, "
            "research, writing, and follow-up for LinkedIn and email, so your reps spend "
            "more time in meetings and closing.",
            "EverWorker generated an additional two point seven million dollars in "
            "pipeline for Memgraph in ninety days, combining their inbound and outbound "
            "signal intelligence — they're now scaling to process one hundred thousand "
            "contacts a month.",
        ],
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
        "presenter_notes": [
            "EverWorker is an autonomous multi-agent system — at its core, multiple SDR "
            "AI agents tailored to your specific GTM; there's no minimum or maximum, we "
            "size it to your GTM and agent count has no impact on pricing. A built-in "
            "context engine means it knows your product, personas, messaging, offers, "
            "case studies, and writing style. The agentic signal intelligence layer "
            "researches technologies, hiring, and news signals, deanonymizes website "
            "traffic, and aligns to your marketing and ABM signals. You invoke it on "
            "flexible triggers — always-on for inbound demo requests, schedules for "
            "outbound, CRM lists and properties, CSV uploads, even chat. And a universal "
            "connector integrates your CRM, its own email and LinkedIn infrastructure, "
            "private LLM endpoints, B2B data providers, and your meeting scheduler.",
            "Once configured it runs fully on its own — no human in the loop required, "
            "though you can hand it a list or a task whenever you want. It brings your "
            "team in when a meeting is booked or a positive reply comes back, and "
            "everything is logged in your CRM just like outreach from any other rep.",
            "Best practices are built in at every level to maximize output, and we coach "
            "your team on human-AI augmentation — AI SDR outreach over email and "
            "LinkedIn combined with human SDRs on the phones works extremely well.",
            "The whole solution is configured for you by a forward-deployed GTM engineer "
            "included in your package. Most customers are fully live in five weeks; the "
            "fastest possible is two weeks, because we purchase your email and LinkedIn "
            "send capacity — included — and the accounts need two weeks to warm.",
        ],
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
        "presenter_notes": [
            "EverWorker is trained on your ICP and buying group, and built-in data "
            "enrichment acquires the full buying group for every account.",
            "It runs company-level and contact-level research to create personalized "
            "email and LinkedIn outreach for every contact in that buying group.",
            "It sends through its own email deliverability infrastructure, built to the "
            "highest standard in the market — the AI SDR lands in the primary inbox, "
            "your domain is protected, and every email and reply is logged to your CRM "
            "automatically. Our team is happy to walk through the details.",
            "It also uses its own built-in LinkedIn infrastructure, including "
            "deliverability and LinkedIn account capacity — safe, secure scale of your "
            "LinkedIn channel, included.",
        ],
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
        "presenter_notes": [
            "Deliverability is the probability an email reaches the inbox instead of "
            "spam — it's a function of sender reputation, infrastructure, and "
            "recipient-side filtering, scored continuously by Google, Microsoft, and the "
            "security gateways in front of corporate inboxes. EverWorker optimizes every "
            "layer: mailboxes and send rate, domain health, authentication, "
            "provider matching, a private warmup pool, and no tracking pixels.",
            "On LinkedIn there are three safeguard layers: ID-verified real rental "
            "profiles, dedicated residential-proxy infrastructure with human-pattern "
            "pacing, and a value-led execution layer capped at one connection request "
            "plus two messages.",
        ],
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
        "presenter_notes": [
            "Pricing plans start at three and a half thousand dollars a month — three "
            "packages, and every one includes the forward-deployed GTM engineer, the "
            "email and LinkedIn infrastructure, and the full configuration.",
            "Most customers are live in five weeks, and go-live support is part of every "
            "package, not an add-on.",
        ],
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

    seeded_ids: set[str] = set()
    for deck in SLIDE_DECKS:
        deck_dir = CONTENT_DIR / deck["dir"]
        slides = sorted(p.name for p in deck_dir.glob("*.png")) if deck_dir.exists() else []
        if not slides:
            continue
        seeded_ids.add(deck["_id"])
        await store.upsert_content_item(
            {
                "_id": deck["_id"],
                "type": "slide_deck",
                "title": deck["title"],
                "description": deck["description"],
                "assets": [f"/content/{deck['dir']}/{name}" for name in slides],
                "presenter_notes": deck.get("presenter_notes") or [],
            }
        )

    for video in VIDEOS:
        if not (CONTENT_DIR / video["file"]).exists():
            continue
        seeded_ids.add(video["_id"])
        await store.upsert_content_item(
            {
                "_id": video["_id"],
                "type": "video",
                "title": video["title"],
                "description": video["description"],
                "assets": [f"/content/{video['file']}"],
            }
        )

    # Content removed or renamed here must not linger from a previous seed
    # (a rebrand would otherwise keep serving the old brand's decks from Mongo).
    await store.prune_content_items(seeded_ids)
