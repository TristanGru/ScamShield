"use client";

import { useEffect, useState } from "react";

interface StatusData {
  online: boolean;
  listening: boolean;
  nest_connected: boolean;
  uptime_seconds: number;
  last_event_at: string | null;
}

function formatLastEvent(lastEventAt: string | null): string {
  if (!lastEventAt) return "No recent alerts";

  const diffMs = Date.now() - new Date(lastEventAt).getTime();
  const mins = Math.floor(diffMs / 60000);

  if (mins < 1) return "Alert just now";
  if (mins < 60) return `Last alert ${mins}m ago`;

  const hours = Math.floor(mins / 60);
  if (hours < 24) return `Last alert ${hours}h ago`;

  return "Last alert over a day ago";
}

export default function StatusBadge() {
  const [status, setStatus] = useState<StatusData | null>(null);

  const poll = async () => {
    try {
      const res = await fetch("/api/status", { cache: "no-store" });
      if (res.ok) setStatus(await res.json());
    } catch {
      setStatus(null);
    }
  };

  useEffect(() => {
    poll();
    const interval = setInterval(poll, 30_000);
    return () => clearInterval(interval);
  }, []);

  /* ── Connecting state ─────────────────────────────────────────── */
  if (!status) {
    return (
      <div className="status-pill status-pill--pending" aria-live="polite" aria-label="Connecting to device">
        <span className="status-dot status-dot--pending" />
        Connecting to device
      </div>
    );
  }

  /* ── Offline state ────────────────────────────────────────────── */
  if (!status.online) {
    return (
      <div className="status-pill status-pill--offline" aria-live="polite" aria-label="Device offline">
        <span className="status-dot status-dot--offline" />
        Device offline
      </div>
    );
  }

  /* ── Online state — consolidated into one line ────────────────── */
  const listeningLabel = status.listening ? "Listening now" : "Online";
  const nestLabel = status.nest_connected ? "Nest connected" : "Nest pending";
  const lastLabel = formatLastEvent(status.last_event_at);

  return (
    <div className="flex flex-wrap items-center gap-2" aria-live="polite">
      <div
        className="status-pill status-pill--online"
        title={`${listeningLabel} · ${nestLabel} · ${lastLabel}`}
      >
        <span
          className="status-dot status-dot--online"
          style={{ animation: status.listening ? "pulse 2s cubic-bezier(0.4,0,0.6,1) infinite" : "none" }}
        />
        {listeningLabel}
      </div>
      <span className="chip">{nestLabel}</span>
      <span className="chip">{lastLabel}</span>
    </div>
  );
}
