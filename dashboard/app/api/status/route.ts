import { getSession } from "@auth0/nextjs-auth0";
import { NextResponse } from "next/server";
import { fetchStatus, checkHealth } from "@/lib/api";

export async function GET() {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const online = await checkHealth();
  if (!online) {
    return NextResponse.json({ online: false, nest_connected: false, listening: false, uptime_seconds: 0, last_event_at: null });
  }

  try {
    const status = await fetchStatus();
    return NextResponse.json({ online: true, ...status });
  } catch {
    return NextResponse.json({ online: false, nest_connected: false, listening: false, uptime_seconds: 0, last_event_at: null });
  }
}
