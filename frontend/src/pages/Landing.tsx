import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PersonaVisual from "../components/PersonaVisual";
import Wordmark from "../components/Wordmark";
import { player } from "../lib/pcmPlayer";
import { createSession, fetchPersona, type Persona } from "../lib/protocol";

export default function Landing() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [persona, setPersona] = useState<Persona | null>(null);

  useEffect(() => {
    fetchPersona()
      .then(setPersona)
      .catch(() => setError("Couldn't reach the backend — is it running?"));
  }, []);

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

  const name = persona?.name ?? "";

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-center py-5">
        <Wordmark className="text-2xl" />
      </header>

      <main className="mx-auto mb-6 flex w-[min(1200px,94vw)] flex-1 overflow-hidden rounded-3xl border border-accent/60 bg-panel shadow-[0_0_60px_-20px_var(--color-accent)]">
        <section className="flex w-[42%] min-w-[320px] flex-col justify-between p-10">
          <h1 className="text-5xl font-semibold leading-tight">
            {persona && (
              <>
                Meet {persona.name},
                <br />
                {persona.tagline}
              </>
            )}
          </h1>

          <div className="space-y-6">
            <p className="max-w-md text-[15px] leading-relaxed text-gray-400">
              {persona?.description ?? ""}
            </p>
            <button
              onClick={start}
              disabled={busy || !persona}
              className="rounded-full bg-accent px-8 py-3.5 text-lg font-semibold text-ink transition hover:bg-accent-dim disabled:opacity-60"
            >
              {busy ? "Connecting…" : `Ask ${name || "Me"} Anything`}
            </button>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <p className="text-xs text-gray-500">
              By continuing you agree to this demo's terms of use. Conversations are
              processed by third-party AI services.
            </p>
          </div>
        </section>

        <section className="stage-backdrop relative flex flex-1 items-center justify-center">
          <PersonaVisual name={name} imageUrl={persona?.image_url} speaking={false} size={340} />
        </section>
      </main>
    </div>
  );
}
