// Gapless PCM playback via scheduled AudioBufferSourceNodes. One module-level
// instance so the AudioContext unlocked by the landing-page click survives the
// SPA route change into the session.

const SAMPLE_RATE = 22050;

export class PcmPlayer {
  private ctx: AudioContext | null = null;
  private gain: GainNode | null = null;
  private nextTime = 0;
  private sources = new Set<AudioBufferSourceNode>();
  private startedSeqs = new Set<number>();
  private startTimers = new Set<number>();

  onUtteranceStart: (seq: number) => void = () => {};
  onDrain: () => void = () => {};

  /** Must be called from a user gesture (the landing CTA click). */
  unlock(): void {
    if (!this.ctx) {
      const Ctx = window.AudioContext ?? (window as any).webkitAudioContext;
      this.ctx = new Ctx();
      this.gain = this.ctx.createGain();
      this.gain.connect(this.ctx.destination);
    }
    if (this.ctx.state === "suspended") void this.ctx.resume();
  }

  get unlocked(): boolean {
    return this.ctx !== null && this.ctx.state === "running";
  }

  setMuted(muted: boolean): void {
    if (this.gain) this.gain.gain.value = muted ? 0 : 1;
  }

  append(seq: number, pcm: Int16Array): void {
    if (!this.ctx || !this.gain || pcm.length === 0) return;
    const buffer = this.ctx.createBuffer(1, pcm.length, SAMPLE_RATE);
    const channel = buffer.getChannelData(0);
    for (let i = 0; i < pcm.length; i++) channel[i] = pcm[i] / 32768;

    const now = this.ctx.currentTime;
    if (this.nextTime < now + 0.05) this.nextTime = now + 0.05;
    const startAt = this.nextTime;

    const source = this.ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(this.gain);
    source.start(startAt);
    this.nextTime += buffer.duration;
    this.sources.add(source);
    source.onended = () => {
      this.sources.delete(source);
      if (this.sources.size === 0) this.onDrain();
    };

    if (!this.startedSeqs.has(seq)) {
      this.startedSeqs.add(seq);
      const delayMs = Math.max(0, (startAt - now) * 1000);
      const timer = window.setTimeout(() => {
        this.startTimers.delete(timer);
        this.onUtteranceStart(seq);
      }, delayMs);
      this.startTimers.add(timer);
    }
  }

  /** Stop everything immediately (interrupt / barge-in). */
  flush(): void {
    for (const timer of this.startTimers) clearTimeout(timer);
    this.startTimers.clear();
    for (const source of this.sources) {
      source.onended = null;
      try {
        source.stop();
      } catch {
        /* already stopped */
      }
    }
    this.sources.clear();
    this.startedSeqs.clear();
    this.nextTime = 0;
    this.onDrain();
  }

  get playing(): boolean {
    return this.sources.size > 0;
  }
}

export const player = new PcmPlayer();
