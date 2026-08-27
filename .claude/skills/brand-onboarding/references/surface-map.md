# Brand surface map

Every file a rebrand touches, what changes in it, and the rules that keep the
result legible. Each surface is a **full-block replacement** — never append or
patch around old-brand content; that is how brand A leaks into brand B.

## 1. `frontend/src/index.css` — the `@theme` block

Rewrite only the `@theme` block. Keep the `--color-name: #hex;` one-per-line
format — `backend/scripts/generate_placeholder_slides.py` parses it by regex.
Every token must be defined (the slide script asserts `ink`, `panel`, `line`,
`accent`, `body`, `muted` exist).

| Token | Role | Derivation |
|---|---|---|
| `--color-accent` | primary brand color: buttons, wordmark accent, rings | brand primary, adjusted for contrast (below) |
| `--color-accent-dim` | accent hover | a slightly darker/deeper step of accent |
| `--color-accent-soft` / `--color-accent-soft-2` | user-bubble / topic-chip text | very light tints of the accent hue (~95% / ~90% lightness) |
| `--color-ink` | page background; text on accent buttons | brand dark neutral, near-black |
| `--color-panel` / `--color-panel-2` | cards / bubbles | ink lightened one and two steps |
| `--color-line` | borders | panel-2 lightened slightly |
| `--color-body` | default text | off-white, tinted toward the brand hue |
| `--color-muted` | secondary text, slide bullets | desaturated mid tone |
| `--color-scrollbar` | scrollbar thumb | between panel-2 and line |
| `--color-stage-from` / `--color-stage-to` | stage radial gradient | brand dark secondary if one exists, else ink hue-shifted toward the accent |
| `--color-orb-glow` / `--color-orb-1` / `--color-orb-2` | fallback avatar orb | accent-hue tints/shades (glow keeps an alpha suffix like `22`) |
| `--font-brand` | all text | brand font first, then the full existing system-stack fallback |

**Contrast rule (hard):** buttons render `text-ink` on `bg-accent`. If the
brand primary is too dark for near-black text (relative lightness roughly
below 55%), use a lighter tint of the same hue as `--color-accent` and the
brand base as `--color-accent-dim`, and add a VALIDATION item noting the
adjustment. The app is a dark theme; keep `ink` dark even for light-themed
brands (their dark neutral or a near-black of their hue) and note that in
VALIDATION too.

## 2. `frontend/index.html`

Title: `<persona name> — <tagline>`. Add `<link rel="icon" href="/favicon.svg">`
(or .png/.ico — whatever was downloaded). If the brand font is on Google
Fonts, add the two `preconnect` links and the stylesheet link before the
title. Never hotlink or bundle a licensed non-Google font — use the closest
Google alternative and add a VALIDATION item naming the real font.

## 3. `frontend/src/brand.ts`

- `wordmark`: use `{ kind: "logo", src: "/brand/logo.svg", alt: "<Company>" }`
  only if the logo is legible on `--color-ink` (a light/white variant, or an
  SVG whose fills you can safely set to a near-`--color-body` value).
  Otherwise use the text form — company name in lowercase or as styled on
  their site, with `accentStart`/`accentEnd` picking a natural split — and add
  "provide a dark-background logo" to VALIDATION.
- `bookMeetingUrl`: the company's demo/contact/booking URL from research. If
  none was found, keep a `#` placeholder ONLY together with a VALIDATION item;
  never leave the previous company's URL.

## 4. Assets — `frontend/public/`

Create the directory if missing (Vite snapshots `publicDir` at server start —
restart `npm run dev` after first creating it). Layout: `favicon.*` at the
root, everything else under `frontend/public/brand/` (clear that directory
first on every run). Served at `/` in dev (Vite) and prod (the SPA catch-all
serves the built `dist/`).

Persona image: **never fabricate a face.** Leave the
`backend/content/persona.*` convention alone; the orb fallback recolors via
the `--color-orb-*` tokens. Offer in VALIDATION: the user may drop a real
`backend/content/persona.png` (or jpg/webp) and restart the backend.

## 5. `backend/app/seed_data.py`

- `PERSONA`: full dict replacement — `_id` (lowercase persona name), `name`,
  `company`, `website`, `tagline`, `description`, `greeting`,
  `default_topics`, per `persona-and-decks.md`. Keep `voice_id`,
  `image_path`, and `mic_disclaimer` lines exactly as they are.
- `SLIDE_DECKS`: replace titles, descriptions, and `presenter_notes` for the
  five archetype decks. Keep the `_id`/`dir` values from
  `persona-and-decks.md` (stable across brands so Mongo upserts stay clean).
  Deck `description` must say *when to show it* — the model picks decks from
  these lines.
- `VIDEOS = []` — the previous brand's demo reel must not survive. A new
  video is a VALIDATION request; when the user supplies one, drop it at
  `backend/content/videos/<name>.mp4` and restore a VIDEOS entry for it.
- Do not touch the `seed()` function.

## 6. `backend/app/orchestrator/prompt.py`

Replace the entire `GTM_KNOWLEDGE` triple-quoted string per
`gtm-template.md`. Never touch `VOICE_RULES` or `build_system_prompt`.

## 7. `backend/scripts/generate_placeholder_slides.py`

Replace only the `DECKS` dict (see Phase 3). Palette, footer, and sync checks
are data-driven — do not edit them.

## 8. Leak sweep (last step of Phase 2)

For each outgoing brand term recorded in Phase 0 (previous company name,
persona name, wordmark text):

```
grep -ri "<term>" frontend/src frontend/index.html backend/app backend/scripts
```

Every hit is a bug; fix it and re-run until clean. `onboarding/` and
`backend/content/` are excluded on purpose (research history and slide PNGs
regenerated in Phase 3). Also check `README.md`'s Content section only if the
user asks for docs updates — repo docs are not a brand surface.

## Out of scope — never touch

`VOICE_RULES`, `build_system_prompt`, `seed()`, `store.py`, the WS protocol,
`config.py` (voice is `ELEVENLABS_VOICE_ID` in `.env` — remind, don't edit),
semantic UI colors (red mic-slash/End, yellow reconnect badge, gray neutrals),
and `roadmap.md`/`reference/`.
