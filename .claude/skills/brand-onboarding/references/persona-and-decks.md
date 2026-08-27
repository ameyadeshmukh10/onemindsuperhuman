# Persona and deck generation rules

## Persona

- **Name**: a short (1-2 syllable) friendly human first name. Alliteration
  with the company name is nice when it comes naturally ("Evie" for
  EverWorker). Never reuse a product, feature, or competitor name that
  appeared in research. Offer three alternatives in VALIDATION — the name is
  the user's call, yours is just the default.
- `_id`: the name, lowercase. (Old persona docs persist harmlessly in Mongo;
  sessions look up the current `_id` only.)
- `company` / `website`: proper company name and bare domain.
- `tagline`: `"Your <Company> Guide"` unless the company's own voice suggests
  something better sourced from their site.
- `description` (landing page paragraph): 2-3 sentences in the shape of the
  current one — who the persona is, what it can show you (only
  verbatim-sourced capabilities), and an invitation. Mention the persona name
  twice at most.
- `greeting` (spoken): 3 sentences — who I am, what I can show you (top 2-3
  allowlisted capabilities), one opening question. Must read naturally aloud.
- `default_topics`: exactly 3 short chips:
  `"What is <Company>?"`, the top capability phrased as a visitor's question,
  and `"Pricing"` — replaced by `"How do we start?"` when pricing is private.
- Keep `voice_id`, `image_path`, `mic_disclaimer` untouched (surface-map.md).

## The five deck archetypes

Stable `_id`s and dirs across every brand — only titles, descriptions, and
notes change. Slide counts are the archetype's range; pick within it and keep
`presenter_notes` length equal to the slide count in both `seed_data.py` and
the generator's `DECKS`.

| `_id` | `dir` | Slides | Story |
|---|---|---|---|
| `overview_deck` | `slides/overview` | 4-5 | what it is → how value flows → the flagship proof point |
| `how_it_works_deck` | `slides/how_it_works` | 3-4 | mechanism/architecture → what runs itself vs. involves humans → implementation/time-to-live |
| `differentiation_deck` | `slides/differentiation` | 3-4 | why this beats the status quo: quality, depth, results — aimed at the category's biggest doubt |
| `trust_deck` | `slides/trust` | 2-3 | safety/reliability/compliance — the objection deep-dive |
| `pricing_deck` | `slides/pricing` | 2 | tiers (or how engagement works, if private) → next steps / book a meeting |

The previous brand may use legacy dirs (e.g. `slides/outreach_quality`,
`slides/infrastructure`); switching to the archetype ids/dirs is correct —
seeding prunes the old items and the generator removes stray dirs.

- Deck `description` fields are how the model picks a deck: state slide count,
  a one-phrase-per-slide summary, and an explicit "Show when …" trigger,
  mirroring the current file's phrasing.
- **Drop rule:** `overview_deck` and `pricing_deck` may never be dropped —
  the GTM Journeys reference them unconditionally. If research genuinely
  cannot fill one of the other three archetypes (nothing on trust/security at
  all), drop that deck — but from `seed_data.py` AND the generator's `DECKS`
  in the same change (the generator's sync assert fails on a mismatch), and
  make sure no GTM section (objections especially) still points a visitor at
  it. Add a VALIDATION item — a missing deck beats an invented one.

## Presenter-note style (spoken verbatim — source-policy rule 7)

- 1-3 sentences per slide, conversational spoken prose. No markdown, no URLs.
- Numbers spelled out the way a voice says them ("two point seven million
  dollars", "ninety days").
- Only allowlisted facts. If a slide needs a fact you don't have, redesign
  the slide around what you do have.
- Note N narrates slide N — order matters, and the first note should work as
  a cold open for the deck.

## Slide outlines (the generator's `DECKS`)

- Keyed by dir basename; one `(title, bullets)` tuple per slide; 2-3 bullets,
  each ≤ 60 characters or so (single line at 38px).
- Titles are claims in the brand's voice, not labels ("Double your pipeline
  this quarter", not "Overview").
- Bullets may compress allowlisted facts; digits are fine on slides (the
  spoken form lives in the notes).

## Deriving the palette

Work from `brand-profile.json`:

1. `accent` = the brand's primary CTA color, contrast-adjusted per
   surface-map.md's hard rule (ink text must stay legible on it).
2. Dark surfaces (`ink`, `panel`, `panel-2`, `line`): if the brand has dark
   neutrals, use them; otherwise keep near-black values hue-shifted toward
   the brand hue (change hue, keep current lightness).
3. `stage-from`/`stage-to` and the orb colors: shades of the brand's
   secondary (or accent) hue at the current tokens' approximate lightness.
4. `body`, `muted`, `scrollbar`, `accent-soft`, `accent-soft-2`: recompute as
   tints of the new hues per the surface-map table — never leave them on the
   old brand's hue.
5. Sanity: view the running app; text must be comfortably readable on every
   surface. When in doubt, keep lightness/contrast of the current values and
   change hue only, then flag color choices for the user in VALIDATION.
