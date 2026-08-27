# Validation checklist and interactive loop

## `onboarding/<slug>/VALIDATION.md` skeleton

```markdown
# <Company> onboarding — validation

Try it first: open http://localhost:5173, click through the landing page, and
have a real conversation with <persona name> — ask what <Company> does, ask
for pricing, ask a hard question, interrupt mid-sentence.

Legend: [ ] open · [x] resolved · [~] deferred by user

## Must confirm (facts the persona states out loud)
- [ ] Proof allowlist — approve each line (from prompt.py "Proof you may cite"):
      <one sub-item per allowlisted customer/metric/quote, with source URL>
- [ ] Pricing — <"confirm these public tiers: …" | "the site publishes no
      pricing, so the persona deflects to a meeting — confirm, or provide
      tiers I should state">
- [ ] Booking URL — CTA points at <url | "none found — provide one">
- [ ] <every open_questions[] item from brand-profile.json, one per line,
      each phrased as a decision or a request for material>

## Should review (identity and look)
- [ ] Persona name "<name>" — alternatives: <alt1>, <alt2>, <alt3>
- [ ] Greeting and suggested topics — say them out loud once
- [ ] Colors — accent <hex> on dark <hex>; <note any contrast adjustments>
- [ ] Wordmark — <logo file | styled text> — provide a dark-background logo
      to upgrade
- [ ] Typography — <font> <"(via Google Fonts)" | "substituted for licensed
      <real font> — provide font files or approve the substitute">

## Materials you can provide (each upgrades the experience)
- [ ] Real slide exports (PNG, 1600×900) to replace placeholders — per deck:
      <deck: slide count and outline summary>
- [ ] A demo video → backend/content/videos/demo.mp4
- [ ] A persona image → backend/content/persona.png (else the initial-orb shows)
- [ ] Voice: set ELEVENLABS_VOICE_ID in .env to a voice that fits
      <persona name> (env-only; the persona is silent-with-text without a key)
```

Fill every `<...>`; delete nothing. Sub-items under the proof allowlist make
the user approve each claim individually — that is the point of the file.

## The loop

1. Present VALIDATION.md to the user (path + the "Must confirm" items inline)
   and ask them to try the app first.
2. Work the list top-to-bottom with AskUserQuestion — at most 4 questions per
   call, one per checklist item, most consequential first (proof, pricing,
   booking URL before aesthetics). Give concrete options ("Keep", "Change to
   …", "Remove") — free-form "Other" is always available. Batch related
   trivia; never re-ask anything already answered.
3. Apply each answer immediately, per surface-map.md:
   - GTM/persona text → edit `prompt.py` / `seed_data.py`, save (the
     reloading backend reseeds; re-run smoke.py after big changes).
   - Slide content → update `seed_data.py` notes AND the generator outlines,
     re-run the generator (Phase 3).
   - Supplied assets → copy into place (public/brand/, backend/content/…);
     real slide exports replace a deck dir's PNGs wholesale (delete
     placeholders first; sortable names `01.png, 02.png, …`; update
     presenter_notes if the slide count changed).
   - A removed proof line → delete it from the allowlist AND from any deck
     note or greeting that used it.
4. Flip the item to `[x]` (or `[~]` if the user defers) in VALIDATION.md
   after each application, so the file always shows live state.
5. When all items are `[x]`/`[~]`: summarize what changed since Phase 4,
   suggest one final try-out, and offer to commit the rebrand (list the
   changed files; do not commit unasked). Remind the user that VALIDATION.md
   and research.md stay in `onboarding/<slug>/` as the record of what was
   approved.

## Update runs

When the user later provides materials or corrections ("here's our real
logo", "pricing changed"), this skill re-enters at Phase 0's update mode:
apply the delta per surface-map.md, re-run the Phase 4 checks, and append the
newly validated items to VALIDATION.md rather than regenerating it.
