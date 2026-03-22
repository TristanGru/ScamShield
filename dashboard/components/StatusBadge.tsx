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

  return "Recent alert on record";
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
      <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-700 px-3 py-1 text-xs text-gray-300">
        <span className="h-2 w-2 rounded-full bg-gray-500" />
        Connecting...
      </span>
    );
  }

  if (!status.online) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-900/40 px-3 py-1 text-xs text-red-400">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        Pi offline
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full bg-green-900/40 px-3 py-1 text-xs text-green-400"
      title={formatLastEvent(status.last_event_at)}
    >
      <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
      {status.listening ? "Listening" : "Online"}
      {status.nest_connected && " - Nest connected"}
    </span>
  );
}
