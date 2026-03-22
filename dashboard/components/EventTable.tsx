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
      <div className="rounded-3xl border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.78),rgba(15,23,42,0.58))] p-8 text-center shadow-[0_24px_80px_rgba(2,6,23,0.28)]">
        <p className="text-lg text-slate-200">No scam activity logged yet.</p>
        <p className="mt-2 text-sm leading-6 text-slate-400">
          Flagged calls, manual reports, and alert details will appear here once ScamShield starts receiving live events.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="hidden items-center gap-4 border-b border-white/10 bg-white/5 px-4 py-3 text-xs uppercase tracking-[0.22em] text-slate-500 sm:flex">
        <span className="w-16">Type</span>
        <span className="w-10 text-center">Score</span>
        <span className="flex-1">Keywords</span>
        <span className="w-32 text-right">Time</span>
        <span className="w-4" />
      </div>

      <div className="overflow-hidden rounded-3xl border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.78),rgba(15,23,42,0.58))] shadow-[0_24px_80px_rgba(2,6,23,0.28)] sm:rounded-t-none">
        {events.map((event) => (
          <EventRow key={event.id} event={event} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex flex-col gap-3 text-sm text-slate-400 sm:flex-row sm:items-center sm:justify-between">
          <span>
            Showing {(page - 1) * limit + 1}-{Math.min(page * limit, total)} of {total}
          </span>
          <div className="flex gap-2">
            {page > 1 && (
              <a
                href={`?page=${page - 1}`}
                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 transition-colors hover:bg-white/10"
              >
                Prev
              </a>
            )}
            {page < totalPages && (
              <a
                href={`?page=${page + 1}`}
                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 transition-colors hover:bg-white/10"
              >
                Next
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
