import { useState } from "react";
import { useNavigate } from "react-router-dom";
import PersonaVisual from "../components/PersonaVisual";
import { player } from "../lib/pcmPlayer";
import { createSession } from "../lib/protocol";

const PERSONA_NAME = "Evie";

export default function Landing() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    player.unlock(); // the click is the user gesture that unlocks audio
    try {
      const session = await createSession();
      navigate(`/session/${session.id}`);
    } catch {
      setError("Couldn't start a session — is the backend running?");
      setBusy(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-center py-5">
        <span className="text-2xl font-bold tracking-tight">
          ever<span className="text-accent">worker</span>
        </span>
      </header>

      <main className="mx-auto mb-6 flex w-[min(1200px,94vw)] flex-1 overflow-hidden rounded-3xl border border-accent/60 bg-panel shadow-[0_0_60px_-20px_var(--color-accent)]">
        <section className="flex w-[42%] min-w-[320px] flex-col justify-between p-10">
          <h1 className="text-5xl font-semibold leading-tight">
            Meet {PERSONA_NAME}, Your
            <br />
            Everworker Guide
          </h1>

          <div className="space-y-6">
            <p className="max-w-md text-[15px] leading-relaxed text-gray-400">
              {PERSONA_NAME} is our AI-powered guide, here to help you discover how
              Everworker gives your team AI workers that actually get work done. Whether
              you're curious about getting started or ready to scale, {PERSONA_NAME} has
              the answers.
            </p>
            <button
              onClick={start}
              disabled={busy}
              className="rounded-full bg-accent px-8 py-3.5 text-lg font-semibold text-ink transition hover:bg-accent-dim disabled:opacity-60"
            >
              {busy ? "Connecting…" : `Ask ${PERSONA_NAME} Anything`}
            </button>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <p className="text-xs text-gray-500">
              By continuing you agree to this demo's terms of use. Conversations are
              processed by third-party AI services.
            </p>
          </div>
        </section>

        <section className="relative flex flex-1 items-center justify-center bg-[radial-gradient(ellipse_at_center,#16233a_0%,#0b1220_70%)]">
          <PersonaVisual name={PERSONA_NAME} speaking={false} size={340} />
        </section>
      </main>
    </div>
  );
}
