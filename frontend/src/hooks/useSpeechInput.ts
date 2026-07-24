import { useCallback, useEffect, useRef, useState } from "react";

// Swappable speech-input boundary (roadmap.md: Deepgram is a drop-in second
// implementation of this same surface). v1: browser Web Speech API — free,
// Chrome/Edge only, cloud-backed.

export type SpeechInputState = {
  supported: boolean;
  listening: boolean;
  interim: string;
};

type Options = {
  enabled: boolean; // mic toggled on by the user
  onFinal: (text: string) => void;
  // fires on partial transcripts — full duplex, so the caller can barge in the
  // moment the visitor starts talking over the persona
  onInterim?: (text: string) => void;
};

export function useSpeechInput({ enabled, onFinal, onInterim }: Options): SpeechInputState {
  const Recognition =
    (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
  const supported = Boolean(Recognition);

  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const recRef = useRef<any>(null);
  const shouldRunRef = useRef(false);
  const onFinalRef = useRef(onFinal);
  onFinalRef.current = onFinal;
  const onInterimRef = useRef(onInterim);
  onInterimRef.current = onInterim;

  const stop = useCallback(() => {
    shouldRunRef.current = false;
    recRef.current?.stop();
    recRef.current = null;
    setListening(false);
    setInterim("");
  }, []);

  const start = useCallback(() => {
    if (!supported || recRef.current) return;
    const rec = new Recognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";
    rec.onresult = (event: any) => {
      let interimText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          const text = result[0].transcript.trim();
          if (text) onFinalRef.current(text);
          setInterim("");
        } else {
          interimText += result[0].transcript;
        }
      }
      if (interimText) {
        setInterim(interimText);
        onInterimRef.current?.(interimText);
      }
    };
    rec.onend = () => {
      recRef.current = null;
      setListening(false);
      // Chrome self-terminates after silence — restart while still wanted
      if (shouldRunRef.current) {
        window.setTimeout(() => {
          if (shouldRunRef.current && !recRef.current) start();
        }, 250);
      }
    };
    rec.onerror = (e: any) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        shouldRunRef.current = false;
      }
    };
    recRef.current = rec;
    shouldRunRef.current = true;
    try {
      rec.start();
      setListening(true);
    } catch {
      recRef.current = null;
    }
  }, [supported]);

  useEffect(() => {
    if (enabled) start();
    else stop();
    return stop;
  }, [enabled, start, stop]);

  return { supported, listening, interim };
}
