import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { player } from "../lib/pcmPlayer";
import type { Persona, ServerEvent, Slide, VideoClip } from "../lib/protocol";
import { fetchSession } from "../lib/protocol";
import { SessionSocket, type ConnectionStatus } from "../lib/wsClient";

export type ChatMessage = { id: string; role: "user" | "assistant"; text: string };
export type MediaState =
  | { kind: "slides"; title: string; slides: Slide[]; index: number }
  | { kind: "video"; video: VideoClip }
  | null;

export type SessionState = {
  phase: "boot" | "ready" | "gone";
  persona: Persona | null;
  status: "idle" | "thinking" | "speaking";
  playing: boolean;
  connection: ConnectionStatus;
  messages: ChatMessage[];
  topics: string[];
  media: MediaState;
  ctaHighlight: boolean;
  avatar: { url: string; token: string } | null;
};

type PendingSentence = { text: string; revealed: boolean; timer: number };
type PendingAction = { seq: number; ev: ServerEvent };

let nextId = 0;
const mkId = () => `m${++nextId}`;

// Sentences reveal when their audio starts playing (caption sync); UI actions
// (slides/topics/CTA) execute once every sentence sequenced before them has
// revealed — so a slide never appears before the sentence introducing it.
export function useSession(sessionId: string) {
  const [state, setState] = useState<SessionState>({
    phase: "boot",
    persona: null,
    status: "idle",
    playing: false,
    connection: "connecting",
    messages: [],
    topics: [],
    media: null,
    ctaHighlight: false,
    avatar: null,
  });

  const socketRef = useRef<SessionSocket | null>(null);
  const sentencesRef = useRef<Map<number, PendingSentence>>(new Map());
  const actionsRef = useRef<PendingAction[]>([]);
  const assistantIdRef = useRef<string | null>(null);

  const applyAction = useCallback((ev: ServerEvent) => {
    setState((s) => {
      switch (ev.type) {
        case "show_slides":
          return { ...s, media: { kind: "slides", title: ev.title, slides: ev.slides, index: 0 } };
        case "go_to_slide":
          return s.media?.kind === "slides"
            ? {
                ...s,
                media: {
                  ...s.media,
                  index: Math.min(s.media.slides.length - 1, Math.max(0, ev.index)),
                },
              }
            : s;
        case "play_video":
          return { ...s, media: { kind: "video", video: ev.video } };
        case "suggested_topics":
          return { ...s, topics: ev.topics };
        case "show_cta":
          return { ...s, ctaHighlight: true };
        default:
          return s;
      }
    });
  }, []);

  const tryFlushActions = useCallback(() => {
    const sentences = sentencesRef.current;
    actionsRef.current = actionsRef.current.filter((action) => {
      for (const [seq, sentence] of sentences) {
        if (seq < action.seq && !sentence.revealed) return true; // keep waiting
      }
      applyAction(action.ev);
      return false;
    });
  }, [applyAction]);

  const revealSentence = useCallback(
    (seq: number) => {
      const sentence = sentencesRef.current.get(seq);
      if (!sentence || sentence.revealed) return;
      sentence.revealed = true;
      window.clearTimeout(sentence.timer);
      const targetId = assistantIdRef.current;
      if (targetId) {
        setState((s) => ({
          ...s,
          messages: s.messages.map((m) =>
            m.id === targetId ? { ...m, text: m.text ? `${m.text} ${sentence.text}` : sentence.text } : m,
          ),
        }));
      }
      tryFlushActions();
    },
    [tryFlushActions],
  );

  const clearPending = useCallback(() => {
    for (const sentence of sentencesRef.current.values()) window.clearTimeout(sentence.timer);
    sentencesRef.current = new Map();
    actionsRef.current = [];
  }, []);

  const handleEvent = useCallback(
    (ev: ServerEvent) => {
      setState((s) => (s.phase === "boot" ? { ...s, phase: "ready" } : s));
      switch (ev.type) {
        case "state":
          setState((s) => ({ ...s, status: ev.status }));
          break;
        case "assistant_start": {
          clearPending();
          const id = mkId();
          assistantIdRef.current = id;
          setState((s) => ({ ...s, messages: [...s.messages, { id, role: "assistant", text: "" }] }));
          break;
        }
        case "sentence": {
          const timer = window.setTimeout(() => revealSentence(ev.seq), 3500);
          sentencesRef.current.set(ev.seq, { text: ev.text, revealed: false, timer });
          break;
        }
        case "audio_failed":
          revealSentence(ev.seq);
          break;
        case "show_slides":
        case "go_to_slide":
        case "play_video":
        case "suggested_topics":
        case "show_cta":
          actionsRef.current.push({ seq: ev.seq, ev });
          tryFlushActions();
          break;
        case "assistant_end":
          // safety: reveal any sentence whose audio never arrives
          for (const seq of sentencesRef.current.keys()) {
            const sentence = sentencesRef.current.get(seq)!;
            if (!sentence.revealed) {
              window.clearTimeout(sentence.timer);
              sentence.timer = window.setTimeout(() => revealSentence(seq), 2500);
            }
          }
          break;
        case "interrupted":
          player.flush();
          clearPending();
          setState((s) => ({ ...s, playing: false }));
          break;
        case "avatar":
          setState((s) => ({ ...s, avatar: { url: ev.url, token: ev.token } }));
          break;
        case "speak_started":
          // avatar mode: backend paces these to the avatar's actual playback
          revealSentence(ev.seq);
          setState((s) => ({ ...s, playing: true }));
          break;
        case "speak_ended":
          // one per turn, after the last utterance's duration has elapsed
          setState((s) => ({ ...s, playing: false }));
          break;
        case "error":
          console.warn("server error event:", ev);
          break;
      }
    },
    [clearPending, revealSentence, tryFlushActions],
  );

  useEffect(() => {
    let cancelled = false;

    fetchSession(sessionId)
      .then((info) => {
        if (cancelled) return;
        setState((s) => ({
          ...s,
          persona: info.persona,
          topics: info.persona.default_topics,
          messages: info.messages
            .filter((m) => m.role === "user" || m.role === "assistant")
            .map((m) => ({ id: mkId(), role: m.role as "user" | "assistant", text: m.text })),
        }));
      })
      .catch(() => !cancelled && setState((s) => ({ ...s, phase: "gone" })));

    const socket = new SessionSocket(sessionId);
    socketRef.current = socket;
    socket.onStatus = (connection) =>
      setState((s) =>
        connection === "expired" ? { ...s, connection, phase: "gone" } : { ...s, connection },
      );
    socket.onEvent = handleEvent;
    socket.onAudio = (_gen, seq, pcm) => player.append(seq, pcm);
    socket.connect();

    player.onUtteranceStart = (seq) => {
      setState((s) => ({ ...s, playing: true }));
      revealSentence(seq);
    };
    player.onDrain = () => setState((s) => ({ ...s, playing: false }));

    // If the user refreshed directly into /session/:id the AudioContext is
    // locked — unlock on the first interaction with the page.
    const unlockOnce = () => player.unlock();
    document.addEventListener("pointerdown", unlockOnce, { once: true });

    return () => {
      cancelled = true;
      document.removeEventListener("pointerdown", unlockOnce);
      socket.close();
      player.flush();
    };
  }, [sessionId, handleEvent, revealSentence]);

  const sendMessage = useCallback((text: string, source: "typed" | "voice" | "topic") => {
    const trimmed = text.trim();
    if (!trimmed) return;
    player.flush(); // barge-in: cut current audio immediately, server confirms via `interrupted`
    setState((s) => ({
      ...s,
      messages: [...s.messages, { id: mkId(), role: "user", text: trimmed }],
      ctaHighlight: s.ctaHighlight,
    }));
    socketRef.current?.send({ type: "user_message", text: trimmed, source });
  }, []);

  const interrupt = useCallback((source?: "voice") => {
    player.flush();
    socketRef.current?.send({ type: "interrupt", ...(source ? { source } : {}) });
  }, []);

  const sendAnalytics = useCallback((name: string, props?: Record<string, unknown>) => {
    socketRef.current?.send({ type: "analytics", name, props: props ?? {} });
  }, []);

  const endSession = useCallback(() => {
    sendAnalytics("end_clicked");
    socketRef.current?.send({ type: "end_session" });
    socketRef.current?.close();
    player.flush();
  }, [sendAnalytics]);

  const setMedia = useCallback((updater: (m: MediaState) => MediaState) => {
    setState((s) => ({ ...s, media: updater(s.media) }));
  }, []);

  return useMemo(
    () => ({ state, sendMessage, interrupt, sendAnalytics, endSession, setMedia }),
    [state, sendMessage, interrupt, sendAnalytics, endSession, setMedia],
  );
}
