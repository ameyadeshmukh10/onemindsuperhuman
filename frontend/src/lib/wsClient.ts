import type { ServerEvent } from "./protocol";

export type ConnectionStatus = "connecting" | "open" | "closed" | "expired";

// One WebSocket per session. Filters stale-generation events/audio after an
// interrupt: the server bumps `gen` and the client drops anything older.
export class SessionSocket {
  private url: string;
  private ws: WebSocket | null = null;
  private maxGen = 0;
  private closedByUs = false;
  private retries = 0;
  private pingTimer: number | null = null;

  onEvent: (ev: ServerEvent) => void = () => {};
  onAudio: (gen: number, seq: number, pcm: Int16Array) => void = () => {};
  onStatus: (s: ConnectionStatus) => void = () => {};

  constructor(sessionId: string) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    this.url = `${proto}://${location.host}/ws/${sessionId}`;
  }

  connect(): void {
    this.onStatus("connecting");
    const ws = new WebSocket(this.url);
    ws.binaryType = "arraybuffer";
    this.ws = ws;

    ws.onopen = () => {
      this.retries = 0;
      this.onStatus("open");
      this.pingTimer = window.setInterval(() => this.send({ type: "ping" }), 25000);
    };

    ws.onmessage = (msg) => {
      if (typeof msg.data === "string") {
        const ev = JSON.parse(msg.data) as ServerEvent;
        if (typeof ev.gen === "number") {
          if (ev.gen < this.maxGen) return; // stale generation
          this.maxGen = ev.gen;
        }
        this.onEvent(ev);
      } else {
        const view = new DataView(msg.data as ArrayBuffer);
        const gen = view.getUint32(0);
        const seq = view.getUint32(4);
        if (gen < this.maxGen) return;
        this.maxGen = gen;
        this.onAudio(gen, seq, new Int16Array((msg.data as ArrayBuffer).slice(8)));
      }
    };

    ws.onclose = (ev) => {
      if (this.pingTimer) window.clearInterval(this.pingTimer);
      this.pingTimer = null;
      if (this.closedByUs) return;
      if (ev.code === 4404) {
        // Session no longer exists server-side — retrying can never succeed.
        this.closedByUs = true;
        this.onStatus("expired");
        return;
      }
      this.onStatus("closed");
      const delay = Math.min(8000, 1000 * 2 ** this.retries++);
      window.setTimeout(() => {
        if (!this.closedByUs) this.connect();
      }, delay);
    };
  }

  send(obj: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(obj));
  }

  close(): void {
    this.closedByUs = true;
    if (this.pingTimer) window.clearInterval(this.pingTimer);
    this.ws?.close();
  }
}
