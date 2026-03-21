import type { ScamEvent } from "@/lib/api";
import EventRow from "./EventRow";

interface EventTableProps {
  events: ScamEvent[];
  total: number;
  page: number;
  limit: number;
}

export default function EventTable({ events, total, page, limit }: EventTableProps) {
  const totalPages = Math.ceil(total / limit);

  if (events.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-8 text-center">
        <p className="text-slate-400">No events logged yet.</p>
        <p className="mt-1 text-sm text-slate-600">Events will appear here when ScamShield detects a suspicious call.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-2 text-xs uppercase tracking-wide text-slate-500 border-b border-slate-800">
        <span className="w-16">Type</span>
        <span className="w-10 text-center">Score</span>
        <span className="flex-1">Keywords</span>
        <span className="w-32 text-right">Time</span>
        <span className="w-4" />
      </div>

      <div className="rounded-b-xl border border-t-0 border-slate-800 bg-slate-900/50 overflow-hidden">
        {events.map((event) => (
          <EventRow key={event.id} event={event} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
          <span>
            Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total}
          </span>
          <div className="flex gap-2">
            {page > 1 && (
              <a
                href={`?page=${page - 1}`}
                className="rounded bg-slate-800 px-3 py-1 hover:bg-slate-700 transition-colors"
              >
                ← Prev
              </a>
            )}
            {page < totalPages && (
              <a
                href={`?page=${page + 1}`}
                className="rounded bg-slate-800 px-3 py-1 hover:bg-slate-700 transition-colors"
              >
                Next →
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
