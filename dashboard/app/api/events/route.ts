import { getSession } from "@auth0/nextjs-auth0";
import { NextRequest, NextResponse } from "next/server";
import { fetchEvents } from "@/lib/api";

export async function GET(req: NextRequest) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const page = parseInt(searchParams.get("page") ?? "1");
  const limit = parseInt(searchParams.get("limit") ?? "20");
  const triggerType = searchParams.get("trigger_type") ?? undefined;

  try {
    const data = await fetchEvents(page, limit, triggerType);
    return NextResponse.json(data);
  } catch (err) {
    console.error("[/api/events] Pi API unreachable:", err);
    return NextResponse.json({ error: "Pi API unreachable", events: [], total: 0 }, { status: 503 });
  }
}
