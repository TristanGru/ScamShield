/**
 * api.ts — Server-side fetch helpers for the Pi FastAPI.
 * The PI_API_URL is never sent to the browser.
 */

const PI_API_URL = process.env.PI_API_URL || "http://localhost:8000";

export interface ScamEvent {
  id: string;
  created_at: string;
  trigger_type: "auto" | "manual";
  scam_score: number | null;
  keywords: string[];
  transcript: string;
  sms_sent: number;
  synced: number;
}

export interface EventsResponse {
  events: ScamEvent[];
  total: number;
}

export interface StatusResponse {
  nest_connected: boolean;
  listening: boolean;
  uptime_seconds: number;
  last_event_at: string | null;
}

export async function fetchEvents(
  page = 1,
  limit = 20,
  triggerType?: string
): Promise<EventsResponse> {
  const offset = (page - 1) * limit;
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (triggerType) params.set("trigger_type", triggerType);

  const res = await fetch(`${PI_API_URL}/events?${params}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Pi API error: ${res.status}`);
  }

  return res.json();
}

export async function fetchStatus(): Promise<StatusResponse> {
  const res = await fetch(`${PI_API_URL}/status`, {
    next: { revalidate: 30 },
  });

  if (!res.ok) {
    throw new Error(`Pi status error: ${res.status}`);
  }

  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${PI_API_URL}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}
