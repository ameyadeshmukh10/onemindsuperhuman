# Source policy — verbatim or nothing

The persona this app runs speaks for a real company, out loud, to that
company's prospects. A single invented customer name, number, or price is a
liability the company never agreed to. These rules are absolute.

1. **Verbatim or nothing.** A fact enters `research.md` (and from there the
   app) only if it appears on a page owned by the company (their domain, or
   their official docs subdomain). Record the exact quote and the source URL.
   Marketing paraphrase is allowed later when writing copy, but only in a
   direction that *weakens or preserves* the claim — never strengthens it
   ("2x more replies" may become "more replies", never "2-3x more replies").

2. **Silence is an answer.** If a page doesn't state something, the answer is
   "not stated" — not an inference. Anything the app needs but the site does
   not state goes into `brand-profile.json.open_questions[]` and becomes a
   VALIDATION.md item.

3. **The proof allowlist is closed.** The GTM prompt's "Proof you may cite
   (and nothing beyond it)" section is the complete universe of customer
   names, quotes, and metrics the persona may ever say. Only verbatim-sourced
   items enter it. Anonymous case studies stay anonymous ("a mid-market
   logistics company"), even if you can guess who they are.

4. **Pricing is binary.** Either the site publishes pricing — then quote it
   exactly (tiers, numbers, billing period) — or it doesn't, and the GTM
   prompt must say: pricing is not published; never state or estimate
   numbers; say pricing is tailored and offer to book a meeting, and treat
   that as the strong answer, not a dodge.

5. **No cross-site synthesis.** Review sites, press, Wikipedia, and
   competitors' comparisons may guide *where you look* on the company's own
   site, but their content never enters the app. WebSearch snippets of the
   company's own pages count as owned content only when you could not fetch
   the page itself — quote the snippet verbatim and mark the entry
   `via search snippet` in research.md.

6. **Regulatory and security claims are exact.** SOC 2, GDPR, HIPAA, ISO —
   copy the exact claim wording. "SOC 2 Type II certified" and "SOC 2
   compliant" are different claims. If the site is vague, the persona deflects
   to a meeting; it never sharpens the claim.

7. **Presenter notes are spoken aloud.** Nothing in `presenter_notes` may be
   a placeholder, a hedge to the operator, or a bracketed TODO. Every note
   must be safe to speak verbatim to a live prospect using only allowlisted
   facts. Placeholders like `[placeholder — see VALIDATION.md]` are fine in
   research.md and in slide *outlines*, never in notes.

8. **Failed fetches are documented, not skipped.** If a page 403s or times
   out, record the URL and failure in research.md, try the WebSearch-snippet
   fallback, and add anything still missing to `open_questions`. If the whole
   site is unfetchable, ask the user directly (brand hexes, logo file, a copy
   of key pages) via AskUserQuestion rather than guessing.

9. **When in doubt, leave it out.** An app that says less but is entirely
   true beats one that says more. The validation loop exists precisely so the
   user can supply what research could not.
