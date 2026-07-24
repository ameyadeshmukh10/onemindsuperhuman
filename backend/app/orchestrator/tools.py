"""Tool definitions and executors.

Tools are UI side effects only — the executor resolves content ids against the
manifest and returns (ui_event | None, tool_result_string). Unknown ids return an
error string so Claude can self-correct on the continuation turn.
"""

from __future__ import annotations

TOOL_DEFINITIONS = [
    {
        "name": "show_slides",
        "description": (
            "Display a slide deck to the user in the media pane. Always speak a sentence "
            "introducing what you're about to show BEFORE calling this. Use it whenever "
            "visual content would help — overview, pricing, how-it-works."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "deck_id": {
                    "type": "string",
                    "description": "Id of a slide_deck item from the content manifest",
                },
                "narrate": {
                    "type": "boolean",
                    "description": (
                        "Default true: the system speaks slide 1's presenter notes "
                        "verbatim for you — never write your own narration for it. "
                        "Pass false ONLY when referencing the deck mid-answer without "
                        "its scripted notes."
                    ),
                },
            },
            "required": ["deck_id"],
        },
    },
    {
        "name": "go_to_slide",
        "description": (
            "While a slide deck is on screen, move it to a specific slide (1-based). "
            "Use it to present a deck the way a rep would: say a sentence or two about "
            "the current slide, call go_to_slide for the next one, then talk about that "
            "one. The deck advances exactly when your narration reaches it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "slide_number": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based slide number within the deck currently shown",
                },
                "narrate": {
                    "type": "boolean",
                    "description": (
                        "Default true: the system speaks this slide's presenter notes "
                        "verbatim for you — never write your own narration for it. "
                        "Pass false ONLY when referencing a slide mid-answer without "
                        "its scripted notes."
                    ),
                },
            },
            "required": ["slide_number"],
        },
    },
    {
        "name": "play_video",
        "description": (
            "Play a demo video clip in the media pane. Always speak a sentence introducing "
            "the clip BEFORE calling this."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "video_id": {
                    "type": "string",
                    "description": "Id of a video item from the content manifest",
                }
            },
            "required": ["video_id"],
        },
    },
    {
        "name": "set_suggested_topics",
        "description": (
            "Replace the suggested-topic chips under the chat with 3 short next-step "
            "topics (2-4 words each). Call this at the end of EVERY reply so the user "
            "always has relevant quick options."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 4,
                }
            },
            "required": ["topics"],
        },
    },
    {
        "name": "show_book_meeting_cta",
        "description": (
            "Highlight the 'Book a Meeting' button. Call when the user shows buying "
            "intent or asks to talk to a human."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _narration(deck: dict, number: int, tool_input: dict) -> tuple[str | None, str]:
    """(verbatim script to speak server-side, result-suffix) for slide `number`.

    Narration defaults ON — the scripted talk track is the product; the model
    opts out explicitly for mid-answer slide references."""
    if tool_input.get("narrate") is False:
        return None, ""
    notes = deck.get("presenter_notes") or []
    if number <= len(notes):
        return notes[number - 1], (
            " Its presenter notes are being spoken for you now — do NOT narrate this "
            "slide yourself; go straight to the next go_to_slide call, or to your one "
            "short closing question if this was the last slide."
        )
    return None, " No presenter notes exist for this slide — describe it briefly yourself."


def execute(
    name: str,
    tool_input: dict,
    content_items: list[dict],
    current_deck_id: str | None = None,
) -> tuple[dict | None, str, str | None]:
    """Returns (ui_event, tool_result_text, verbatim_speech_or_None)."""
    items = {item["_id"]: item for item in content_items}

    if name == "show_slides":
        deck = items.get(tool_input.get("deck_id", ""))
        if not deck or deck["type"] != "slide_deck":
            available = [i for i, item in items.items() if item["type"] == "slide_deck"]
            return None, f"error: unknown deck_id; available slide decks: {available}", None
        slides = [
            {"id": f"{deck['_id']}:{n}", "url": url, "title": deck["title"]}
            for n, url in enumerate(deck["assets"])
        ]
        speech, suffix = _narration(deck, 1, tool_input)
        return (
            {
                "type": "show_slides",
                "deck_id": deck["_id"],
                "title": deck["title"],
                "slides": slides,
            },
            f"ok — deck is visible on slide 1 of {len(slides)}.{suffix}",
            speech,
        )

    if name == "go_to_slide":
        try:
            number = int(tool_input.get("slide_number", 0))
        except (TypeError, ValueError):
            number = 0
        if number < 1:
            return None, "error: slide_number must be a 1-based integer", None
        deck = items.get(current_deck_id or "")
        if not deck:
            return {"type": "go_to_slide", "index": number - 1}, f"ok — deck is on slide {number}", None
        total = len(deck.get("assets") or [])
        if total and number > total:
            return None, f"error: this deck has {total} slides", None
        speech, suffix = _narration(deck, number, tool_input)
        return (
            {"type": "go_to_slide", "index": number - 1},
            f"ok — deck is on slide {number} of {total}.{suffix}",
            speech,
        )

    if name == "play_video":
        video = items.get(tool_input.get("video_id", ""))
        if not video or video["type"] != "video":
            available = [i for i, item in items.items() if item["type"] == "video"]
            return None, f"error: unknown video_id; available videos: {available}", None
        return {
            "type": "play_video",
            "video": {"id": video["_id"], "url": video["assets"][0], "title": video["title"]},
        }, "ok — video is now playing", None

    if name == "set_suggested_topics":
        topics = [str(t)[:40] for t in tool_input.get("topics", [])][:4]
        if not topics:
            return None, "error: topics must be a non-empty list of short strings", None
        return {"type": "suggested_topics", "topics": topics}, "ok", None

    if name == "show_book_meeting_cta":
        return {"type": "show_cta", "cta": "book_meeting"}, "ok — the button is highlighted", None

    return None, f"error: unknown tool {name}", None
