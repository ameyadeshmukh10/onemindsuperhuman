# Roadmap — Everworker Superhuman

A phased plan for evolving this prototype from audio-only (v1) to a full 1mind-style
interactive avatar experience. Decisions below were made deliberately — cost-conscious
first, avatar streaming later.

---

## v1 — Audio-only Superhuman (current build)

- **Voice**: ElevenLabs streaming TTS (`eleven_flash_v2_5`, PCM over WebSocket, per-sentence
  streams with lookahead). Voice is configurable via `ELEVENLABS_VOICE_ID`.
- **Persona**: static persona visual (image or generated avatar) with a speaking pulse —
  no video streaming. Drop a `persona.jpg` into `backend/content/` to use a real image.
- **Brain**: Claude (`claude-sonnet-5` by default, configurable via `ANTHROPIC_MODEL`) with
  tool use for `show_slides`, `play_video`, `set_suggested_topics`, `show_book_meeting_cta`.
- **Voice input**: browser Web Speech API (see "Voice input upgrades" below).
- **Why audio-only first**: avatar streaming is the most expensive component to run
  (~$0.10–0.20/min); nailing orchestration, content, and conversation quality first means
  avatar minutes are only spent once the experience is worth streaming.

## v2 — Branded Everworker mascot avatar (NEXT PRIORITY)

Replace the static persona with an animated **Everworker mascot character** (the 1mind
JFrog deployment uses "Arty", an illustrated frog — same idea).

- Requires: an illustrated mascot design (single high-quality still is enough to start).
- Candidate providers that animate stills / stylized characters:
  - **HeyGen photo avatar** — animate an uploaded image; most mature ecosystem.
  - **LemonSlice** — image-to-avatar with gestures, built for stylized characters.
  - **Hedra** — character animation from a still.
- Caveat: quality for non-photoreal characters is more experimental than photoreal humans —
  prototype with one provider behind the `AvatarDriver` boundary before committing.
- Architecture note: the backend already isolates speech behind the TTS relay
  (`backend/app/services/tts.py`). The avatar integration replaces/wraps this service:
  instead of relaying PCM to the client, sentences get sent to the avatar provider's
  session and the client renders their WebRTC video stream.

## v3 — Photoreal interactive avatar streaming

Full 1mind-style talking persona video.

- **Primary choice: HeyGen Interactive Avatar / LiveAvatar API**
  - ~$0.10–0.20/min; LiveKit-based JS SDK; text-driven "repeat" mode fits our
    orchestrator (we send sentences, avatar speaks them lip-synced).
  - Best idle/talking behavior in 2026 comparisons; chosen by Docket for the same
    use case over Tavus/Anam/Simli.
  - Supports ElevenLabs voice linking, custom avatars, photo avatars.
  - Concurrency: ~20 sessions on Essential plan; 20-min session cap.
- **Budget/latency alternative: Anam** — ~180ms latency, $0.11–0.16/min, 50 free
  minutes, direct ElevenLabs voice integration, "custom LLM" mode where their infra
  handles STT+TTS+avatar around our Python brain. Only ~5 concurrent sessions.
- **Premium alternative: Tavus** — most photoreal (Phoenix-4), <500ms, ~$395/mo tier.
- Integration shape: backend mints a provider session token → frontend swaps
  `PersonaStage` for the provider's video stream component → orchestrator sends
  sentences to the provider session instead of (or alongside) the TTS relay.

## Voice input upgrades (fallback / discussion items)

v1 uses the **browser Web Speech API** — free, zero backend work, but effectively
Chrome/Edge-only and cloud-backed (audio goes to Google). Options if/when this is
insufficient:

1. **Deepgram streaming STT** (recommended upgrade) — cross-browser, accurate,
   ~$0.006/min, $200 free credit. Frontend streams mic audio over our existing
   WebSocket → backend relays to Deepgram → transcripts feed the orchestrator.
   The frontend already abstracts speech input behind the `SpeechInput` interface
   (`frontend/src/hooks/useSpeechInput.ts`) so this is a drop-in second implementation.
2. **Avatar provider built-in STT** — e.g. Anam's custom-LLM mode handles STT for you.
   Least code, but couples voice input to the avatar vendor's conversation loop.
3. **Full-duplex barge-in** — v1 is half-duplex (mic pauses while the persona speaks,
   to avoid the persona hearing itself). True barge-in needs echo cancellation
   (browser AEC + interruption-on-voice-activity) — revisit alongside Deepgram.

## Custom human persona clone (documented capability — deprioritized)

Providers (HeyGen, Tavus) can clone a real person (e.g. an Everworker teammate) from
a few minutes of captured footage, producing a photoreal custom avatar with their voice.
**We will likely never use this** — it adds capture logistics, consent/likeness
considerations, setup cost, and per-avatar fees — but it is a capability of the chosen
provider stack and remains available if a "real spokesperson" persona is ever wanted.

## Other noted upgrades

- **ElevenLabs WebSocket stream-input** (`/v1/text-to-speech/{voice}/stream-input`) with
  character-alignment timestamps → word-level caption sync and better prosody across
  sentences (v1 uses per-sentence HTTP streams with `previous_text` for continuity).
- **WS flow control / backpressure** for slow mobile clients (v1 relies on WS buffering).
- **Auth + multi-tenancy** — multiple personas/deployments (one per prospect account,
  like 1mind's per-customer superhumans), session links with prospect identity.
- **Lead capture + CRM push** — book-a-meeting flow wired to a real calendar; session
  transcripts/analytics pushed to HubSpot.
- **Knowledge/RAG layer** — ground answers in Everworker docs (1mind's "GTM Brain"
  equivalent) instead of relying on the system prompt alone.
