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

  return "Recent alert recorded";
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

  if (!status) {
    return (
      <div className="status-chip status-chip--pending" aria-live="polite">
        <span className="h-2.5 w-2.5 rounded-full bg-sky-300" />
        Connecting to device
      </div>
    );
  }

  if (!status.online) {
    return (
      <div className="status-chip status-chip--offline" aria-live="polite">
        <span className="h-2.5 w-2.5 rounded-full bg-rose-300" />
        Device offline
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3" title={formatLastEvent(status.last_event_at)}>
      <div className="status-chip status-chip--online" aria-live="polite">
        <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-emerald-300" />
        {status.listening ? "Listening now" : "Online"}
      </div>
      <div className="utility-chip text-xs">
        {status.nest_connected ? "Nest speaker connected" : "Nest speaker pending"}
      </div>
      <div className="utility-chip text-xs">{formatLastEvent(status.last_event_at)}</div>
    </div>
  );
}
