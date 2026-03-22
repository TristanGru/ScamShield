/**
 * DELETE /api/events/[id]
 * Proxies the delete request to the Pi FastAPI server.
 * Runs server-side — PI_API_URL is never exposed to the browser.
 */
import { getSession } from "@auth0/nextjs-auth0";
import { NextRequest, NextResponse } from "next/server";

const PI_API_URL = process.env.PI_API_URL || "http://localhost:8000";

export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = params;
  if (!id) {
    return NextResponse.json({ error: "Missing event id" }, { status: 400 });
  }

  try {
    const piRes = await fetch(`${PI_API_URL}/events/${id}`, {
      method: "DELETE",
    });

    if (piRes.status === 404) {
      return NextResponse.json({ error: "Event not found" }, { status: 404 });
    }
    if (!piRes.ok) {
      return NextResponse.json({ error: "Pi API error" }, { status: 502 });
    }

    return NextResponse.json({ deleted: id });
  } catch {
    return NextResponse.json({ error: "Could not reach Pi" }, { status: 503 });
  }
}
