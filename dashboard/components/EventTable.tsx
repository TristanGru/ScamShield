"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { ScamEvent } from "@/lib/api";
import EventRow from "./EventRow";

interface EventTableProps {
  events: ScamEvent[];
  total: number;
  page: number;
  limit: number;
}

/* ── Empty state ──────────────────────────────────────────────────────── */
function EmptyState() {
  return (
    <div className="surface" style={{ overflow: "hidden" }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "180px 1fr",
        }}
        className="block sm:grid"
      >
        {/* Left — label */}
        <div
          style={{
            padding: "20px",
            borderRight: "1px solid var(--color-line-subtle)",
            backgroundColor: "rgba(255,255,255,0.02)",
          }}
        >
          <p className="kicker">Event log</p>
          <p
            style={{
              marginTop: "12px",
              fontSize: "18px",
              fontWeight: 600,
              color: "var(--color-ink-primary)",
              lineHeight: 1.2,
            }}
          >
            No activity yet
          </p>
        </div>
        {/* Right — explanation */}
        <div style={{ padding: "20px" }}>
          <p
            style={{
              fontSize: "14px",
              lineHeight: 1.65,
              color: "var(--color-ink-secondary)",
            }}
          >
            Flagged calls, manual reports, and call transcripts will appear here once
            the device begins receiving live events from the home setup.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function EventTable({ events: initialEvents, total, page, limit }: EventTableProps) {
  const [events, setEvents] = useState<ScamEvent[]>(initialEvents);
  const router = useRouter();
  const totalPages = Math.ceil(total / limit);

  function handleDeleted(id: string) {
    setEvents((prev) => prev.filter((e) => e.id !== id));
    router.refresh(); // re-fetch server data to stay in sync
  }

  if (events.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="surface" style={{ overflow: "hidden" }}>

      {/* ── Column header ─────────────────────────────────────────── */}
      <div
        className="hidden lg:grid"
        style={{
          gridTemplateColumns: "130px 72px 1fr 160px 20px",
          gap: "16px",
          padding: "10px 20px",
          borderBottom: "1px solid var(--color-line-subtle)",
          backgroundColor: "rgba(255,255,255,0.02)",
        }}
      >
        <span className="kicker">Trigger</span>
        <span className="kicker">Score</span>
        <span className="kicker">Keywords</span>
        <span className="kicker" style={{ textAlign: "right" }}>Recorded</span>
        <span />
      </div>

      {/* ── Event rows ────────────────────────────────────────────── */}
      <div>
        {events.map((event) => (
          <EventRow key={event.id} event={event} onDeleted={handleDeleted} />
        ))}
      </div>

      {/* ── Pagination ────────────────────────────────────────────── */}
      {totalPages > 1 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
            padding: "14px 20px",
            borderTop: "1px solid var(--color-line-subtle)",
          }}
        >
          <span
            style={{
              fontSize: "13px",
              color: "var(--color-ink-muted)",
            }}
          >
            Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total} events
          </span>

          <div style={{ display: "flex", gap: "8px" }}>
            {page > 1 && (
              <a href={`?page=${page - 1}`} className="btn-quiet">
                ← Previous
              </a>
            )}
            {page < totalPages && (
              <a href={`?page=${page + 1}`} className="btn-quiet">
                Next →
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
