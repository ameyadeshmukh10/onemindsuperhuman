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
                }
            },
            "required": ["deck_id"],
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


def execute(name: str, tool_input: dict, content_items: list[dict]) -> tuple[dict | None, str]:
    items = {item["_id"]: item for item in content_items}

    if name == "show_slides":
        deck = items.get(tool_input.get("deck_id", ""))
        if not deck or deck["type"] != "slide_deck":
            available = [i for i, item in items.items() if item["type"] == "slide_deck"]
            return None, f"error: unknown deck_id; available slide decks: {available}"
        slides = [
            {"id": f"{deck['_id']}:{n}", "url": url, "title": deck["title"]}
            for n, url in enumerate(deck["assets"])
        ]
        return {"type": "show_slides", "deck_id": deck["_id"], "title": deck["title"], "slides": slides}, "ok — slides are now visible"

    if name == "play_video":
        video = items.get(tool_input.get("video_id", ""))
        if not video or video["type"] != "video":
            available = [i for i, item in items.items() if item["type"] == "video"]
            return None, f"error: unknown video_id; available videos: {available}"
        return {
            "type": "play_video",
            "video": {"id": video["_id"], "url": video["assets"][0], "title": video["title"]},
        }, "ok — video is now playing"

    if name == "set_suggested_topics":
        topics = [str(t)[:40] for t in tool_input.get("topics", [])][:4]
        if not topics:
            return None, "error: topics must be a non-empty list of short strings"
        return {"type": "suggested_topics", "topics": topics}, "ok"

    if name == "show_book_meeting_cta":
        return {"type": "show_cta", "cta": "book_meeting"}, "ok — the button is highlighted"

    return None, f"error: unknown tool {name}"
