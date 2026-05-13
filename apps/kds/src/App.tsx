import { useEffect, useMemo, useRef, useState } from "react";
import {
  kitchenQueueCards,
  type KitchenQueueCard,
  type LiveEvent,
  type PlatformOverview
} from "@mypos/domain";
import { apiBaseUrl, kdsHeaders, toWsUrl } from "./api";

const badgeMap: Record<string, string> = {
  RED: "state-red",
  YELLOW: "state-yellow",
  BLUE: "state-blue",
  PURPLE: "state-purple",
  GREEN: "state-green"
};

const priorityOrder: Record<string, number> = { URGENT: 0, HIGH: 1, NORMAL: 2 };

const SLA_WARN = 12;
const SLA_CRIT = 18;

function beep() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.35, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
    osc.start();
    osc.stop(ctx.currentTime + 0.25);
  } catch {
    // blocked before user gesture
  }
}

export default function App() {
  const fallbackCards = useMemo(() => kitchenQueueCards, []);
  const [cards, setCards] = useState<KitchenQueueCard[]>(fallbackCards);
  const [connectionState, setConnectionState] = useState("Fallback demo data");
  const [busyCardId, setBusyCardId] = useState<string | null>(null);
  const [stationFilter, setStationFilter] = useState("ALL");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [tickOffset, setTickOffset] = useState(0);

  const syncTimeRef = useRef(Date.now());
  const prevCountRef = useRef(cards.length);

  // Tick elapsed time locally every 30 s
  useEffect(() => {
    const id = setInterval(() => {
      setTickOffset(Math.floor((Date.now() - syncTimeRef.current) / 60_000));
    }, 30_000);
    return () => clearInterval(id);
  }, []);

  // Beep on new order
  useEffect(() => {
    if (cards.length > prevCountRef.current) beep();
    prevCountRef.current = cards.length;
  }, [cards.length]);

  // Fullscreen change listener
  useEffect(() => {
    const handler = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const applyCards = (next: KitchenQueueCard[]) => {
    setCards(next);
    syncTimeRef.current = Date.now();
    setTickOffset(0);
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => undefined);
    } else {
      document.exitFullscreen().catch(() => undefined);
    }
  };

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/kitchen`);
        const data = (await res.json()) as KitchenQueueCard[];
        if (mounted) { applyCards(data); setConnectionState("Connected to API"); }
      } catch {
        if (mounted) setConnectionState("API offline, showing local queue");
      }
    };
    load().catch(() => undefined);
    return () => { mounted = false; };
  }, [fallbackCards]);

  useEffect(() => {
    let socket: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectDelay = 1_000;
    let destroyed = false;

    const connect = () => {
      if (destroyed) return;
      socket = new WebSocket(toWsUrl(apiBaseUrl));
      socket.onopen = () => {
        setConnectionState("Live websocket connected");
        reconnectDelay = 1_000;
      };
      socket.onerror = () => setConnectionState("Websocket error — reconnecting");
      socket.onclose = () => {
        if (destroyed) return;
        setConnectionState(`Websocket disconnected — reconnecting in ${reconnectDelay / 1000}s`);
        reconnectTimer = setTimeout(connect, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, 30_000);
      };
      socket.onmessage = (msg) => {
        const event = JSON.parse(msg.data) as LiveEvent;
        if (event.type === "snapshot") {
          applyCards((event.payload as PlatformOverview).kitchen);
        }
      };
    };

    connect();
    return () => {
      destroyed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  const runKitchenAction = async (
    cardId: string,
    action: "acknowledge" | "ready" | "out-of-stock"
  ) => {
    try {
      setBusyCardId(cardId);
      const res = await fetch(`${apiBaseUrl}/api/kitchen/${cardId}/${action}`, {
        method: "POST",
        headers: kdsHeaders,
        body: "{}"
      });
      if (!res.ok) throw new Error("Request failed");
      setConnectionState(`Last action: ${action}`);
    } catch {
      setConnectionState("Action failed, API may be offline");
    } finally {
      setBusyCardId(null);
    }
  };

  const stations = useMemo(
    () => ["ALL", ...Array.from(new Set(cards.map((c) => c.station)))],
    [cards]
  );

  const filteredCards = useMemo(() => {
    const base = stationFilter === "ALL" ? cards : cards.filter((c) => c.station === stationFilter);
    return [...base].sort((a, b) => {
      const pa = priorityOrder[a.priority] ?? 3;
      const pb = priorityOrder[b.priority] ?? 3;
      if (pa !== pb) return pa - pb;
      return (b.elapsedMinutes + tickOffset) - (a.elapsedMinutes + tickOffset);
    });
  }, [cards, stationFilter, tickOffset]);

  const hotCount = cards.filter((c) => c.station === "HOT").length;
  const barCount = cards.filter((c) => c.station === "BAR").length;
  const warnCount = cards.filter((c) => c.elapsedMinutes + tickOffset >= SLA_WARN).length;
  const critCount = cards.filter((c) => c.elapsedMinutes + tickOffset >= SLA_CRIT).length;

  return (
    <main className="kds-page">
      <header className="kds-header">
        <div>
          <p className="eyebrow">Kitchen Display System</p>
          <h1>Night Kitchen Board</h1>
        </div>
        <div className="kds-alerts">
          <span className={critCount > 0 ? "tag-crit" : ""}>{connectionState}</span>
          {critCount > 0 ? <span className="tag-crit">⚠ {critCount} OVERDUE</span> : null}
          <button type="button" className="btn-fs" onClick={toggleFullscreen}>
            {isFullscreen ? "✕ Exit Fullscreen" : "⛶ Fullscreen"}
          </button>
        </div>
      </header>

      <section className="kds-summary">
        <div>
          <strong>Hot Station</strong>
          <p>{hotCount} active cards</p>
        </div>
        <div>
          <strong>Bar</strong>
          <p>{barCount} drink queue</p>
        </div>
        <div className={warnCount > 0 ? "sum-warn" : ""}>
          <strong>SLA Warning ≥{SLA_WARN} min</strong>
          <p>{warnCount} orders</p>
        </div>
        <div className={critCount > 0 ? "sum-crit" : ""}>
          <strong>Overdue ≥{SLA_CRIT} min</strong>
          <p>{critCount} orders</p>
        </div>
      </section>

      <div className="station-tabs">
        {stations.map((s) => (
          <button
            key={s}
            type="button"
            className={`station-tab ${stationFilter === s ? "is-active" : ""}`}
            onClick={() => setStationFilter(s)}
          >
            {s}
            <span className="tab-badge">
              {s === "ALL" ? cards.length : cards.filter((c) => c.station === s).length}
            </span>
          </button>
        ))}
      </div>

      <section className="board">
        {filteredCards.map((card) => {
          const elapsed = card.elapsedMinutes + tickOffset;
          const slaPct = Math.min((elapsed / SLA_CRIT) * 100, 100);
          const urgencyClass = elapsed >= SLA_CRIT ? "sla-overdue" : elapsed >= SLA_WARN ? "sla-warning" : "";

          return (
            <article key={card.id} className={`queue-card ${badgeMap[card.colorState]} ${urgencyClass}`}>
              <div className="queue-top">
                <div>
                  <p>{card.station}</p>
                  <h2>{card.ticketNo}</h2>
                </div>
                <div className="chip-group">
                  <span className={card.priority === "URGENT" ? "chip-urgent" : ""}>{card.priority}</span>
                  <span className={elapsed >= SLA_WARN ? "chip-warn" : ""}>{elapsed} min</span>
                </div>
              </div>

              <div className="sla-track">
                <div
                  className={`sla-fill ${slaPct >= 100 ? "sla-fill-crit" : slaPct >= (SLA_WARN / SLA_CRIT) * 100 ? "sla-fill-warn" : ""}`}
                  style={{ width: `${slaPct}%` }}
                />
              </div>

              <div className="table-line">
                <strong>{card.tableLabel}</strong>
                <span>{card.note}</span>
              </div>

              <ul>
                {card.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>

              <div className="actions">
                <button
                  type="button"
                  disabled={busyCardId === card.id}
                  onClick={() => runKitchenAction(card.id, "acknowledge")}
                >
                  รับออเดอร์
                </button>
                <button
                  type="button"
                  disabled={busyCardId === card.id}
                  onClick={() => runKitchenAction(card.id, "ready")}
                >
                  เสร็จแล้ว
                </button>
                <button
                  type="button"
                  disabled={busyCardId === card.id}
                  onClick={() => runKitchenAction(card.id, "out-of-stock")}
                >
                  แจ้งหมด
                </button>
              </div>
            </article>
          );
        })}
        {filteredCards.length === 0 ? (
          <div className="empty-queue">
            <p>ไม่มีออเดอร์ในคิวตอนนี้</p>
          </div>
        ) : null}
      </section>
    </main>
  );
}
