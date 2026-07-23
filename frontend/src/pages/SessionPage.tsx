import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import BottomBar from "../components/BottomBar";
import ChatPanel from "../components/ChatPanel";
import LoadingScreen from "../components/LoadingScreen";
import MediaOverlay from "../components/MediaOverlay";
import PersonaVisual from "../components/PersonaVisual";
import { useSession } from "../hooks/useSession";
import { useSpeechInput } from "../hooks/useSpeechInput";
import { player } from "../lib/pcmPlayer";

export default function SessionPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const { state, sendMessage, sendAnalytics, endSession, setMedia } = useSession(sessionId);
  const [micOn, setMicOn] = useState(false);
  const [speakerOn, setSpeakerOn] = useState(true);

  const speech = useSpeechInput({
    enabled: micOn,
    gated: state.status !== "idle" || state.playing, // half-duplex: don't hear ourselves
    onFinal: (text) => sendMessage(text, "voice"),
  });

  useEffect(() => {
    player.setMuted(!speakerOn);
  }, [speakerOn]);

  const toggleMic = useCallback(() => {
    setMicOn((on) => {
      sendAnalytics("mic_toggled", { on: !on });
      return !on;
    });
  }, [sendAnalytics]);

  const handleEnd = useCallback(() => {
    endSession();
    navigate("/");
  }, [endSession, navigate]);

  if (state.phase === "gone") {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <p className="text-gray-300">This session has expired.</p>
        <Link to="/" className="rounded-full bg-accent px-6 py-2.5 font-semibold text-ink">
          Start a new conversation
        </Link>
      </div>
    );
  }

  const persona = state.persona;

  return (
    <div className="flex h-full flex-col">
      {state.phase === "boot" && <LoadingScreen label={`Waking up ${persona?.name ?? "your guide"}…`} />}

      <header className="flex items-center justify-center py-4">
        <span className="text-xl font-bold tracking-tight">
          ever<span className="text-accent">worker</span>
        </span>
      </header>

      <main className="mx-auto mb-5 flex w-[min(1280px,96vw)] flex-1 flex-col overflow-hidden rounded-3xl border border-accent/60 bg-panel shadow-[0_0_60px_-20px_var(--color-accent)]">
        <div className="flex min-h-0 flex-1">
          <ChatPanel
            messages={state.messages}
            topics={state.topics}
            status={state.status}
            micDisclaimer={persona?.mic_disclaimer ?? ""}
            interim={speech.interim}
            onSend={(text, source) => sendMessage(text, source)}
          />

          <section className="relative flex flex-1 items-center justify-center bg-[radial-gradient(ellipse_at_center,#16233a_0%,#0b1220_70%)]">
            <div
              className={`transition-all duration-500 ${
                state.media ? "absolute bottom-6 right-6 z-20 scale-[0.35] origin-bottom-right" : ""
              }`}
            >
              <PersonaVisual
                name={persona?.name ?? "E"}
                imageUrl={persona?.image_url}
                speaking={state.playing}
                size={300}
              />
            </div>
            {!state.media && persona && (
              <div className="pointer-events-none absolute bottom-8 text-center">
                <p className="text-lg font-semibold">{persona.name}</p>
                <p className="text-sm text-gray-400">{persona.tagline}</p>
              </div>
            )}

            {state.media && (
              <MediaOverlay
                media={state.media}
                onNavigate={(delta) =>
                  setMedia((m) =>
                    m && m.kind === "slides"
                      ? { ...m, index: Math.min(m.slides.length - 1, Math.max(0, m.index + delta)) }
                      : m,
                  )
                }
                onClose={() => {
                  sendAnalytics("media_closed");
                  setMedia(() => null);
                }}
                onVideoEnded={() => sendAnalytics("video_completed")}
              />
            )}

            {state.connection !== "open" && state.phase === "ready" && (
              <div className="absolute top-4 rounded-full border border-yellow-500/40 bg-yellow-500/10 px-4 py-1 text-xs text-yellow-200">
                Reconnecting…
              </div>
            )}
          </section>
        </div>

        <BottomBar
          micOn={micOn}
          micSupported={speech.supported}
          listening={speech.listening}
          speakerOn={speakerOn}
          ctaHighlight={state.ctaHighlight}
          onToggleMic={toggleMic}
          onToggleSpeaker={() => setSpeakerOn((on) => !on)}
          onBookMeeting={() => sendAnalytics("cta_click", { cta: "book_meeting" })}
          onEnd={handleEnd}
        />
      </main>
    </div>
  );
}
