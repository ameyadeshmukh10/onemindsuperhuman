"""Generate placeholder slide PNGs into backend/content/slides/.

Run once (committed output): uv run python scripts/generate_placeholder_slides.py
Replace these with real Everworker deck exports when available.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CONTENT = Path(__file__).resolve().parent.parent / "content"

BG = (11, 15, 20)
CARD = (17, 23, 31)
ACCENT = (74, 222, 128)
TEXT = (236, 240, 244)
MUTED = (148, 163, 178)

DECKS = {
    "overview": [
        ("Meet your AI workers", [
            "Autonomous digital teammates that finish real work",
            "Designed by your team with a no-code builder",
            "Running on schedules, triggers, and conversations",
        ]),
        ("Works inside your stack", [
            "Connects to the tools you already use",
            "Scoped credentials — workers only touch what you allow",
            "Humans stay in the loop where you want approvals",
        ]),
        ("Example roles", [
            "GTM research worker: accounts briefed before every call",
            "Inbox triage worker: routed, drafted, logged",
            "Reporting worker: the Monday report writes itself",
        ]),
    ],
    "pricing": [
        ("Simple pricing", [
            "Plans scale with the number of active workers",
            "Every plan includes the builder and integrations",
            "Start small - add workers as they earn their keep",
        ]),
        ("What's included", [
            "No-code worker builder and templates",
            "Knowledge memories and data collections",
            "Schedules, webhooks, and human approval steps",
        ]),
        ("Getting started", [
            "Pilot with one high-value workflow",
            "Go live in days, not quarters",
            "Book a meeting for a tailored estimate",
        ]),
    ],
}


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def render(deck: str, index: int, title: str, bullets: list[str]) -> None:
    img = Image.new("RGB", (1600, 900), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 60, 1540, 840], radius=28, fill=CARD, outline=(31, 41, 55), width=2)
    d.rectangle([120, 150, 168, 162], fill=ACCENT)
    d.text((120, 200), title, font=_font(64), fill=TEXT)
    y = 360
    for bullet in bullets:
        d.ellipse([124, y + 16, 140, y + 32], fill=ACCENT)
        d.text((170, y), bullet, font=_font(38), fill=MUTED)
        y += 110
    d.text((120, 770), f"Everworker — placeholder slide {index + 1}", font=_font(24), fill=(75, 85, 99))
    out = CONTENT / "slides" / deck
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / f"{index + 1:02d}.png")


if __name__ == "__main__":
    for deck, slides in DECKS.items():
        for i, (title, bullets) in enumerate(slides):
            render(deck, i, title, bullets)
    print("placeholder slides written to", CONTENT / "slides")
