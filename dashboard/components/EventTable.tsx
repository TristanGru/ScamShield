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
      <div className="surface overflow-hidden">
        <div className="grid gap-0 lg:grid-cols-[220px_1fr]">
          <div className="border-b border-white/10 bg-white/[0.03] px-5 py-5 lg:border-b-0 lg:border-r">
            <p className="section-label">Event Log</p>
            <p className="mt-3 text-2xl font-semibold text-white">No activity yet</p>
          </div>
          <div className="px-5 py-5">
            <p className="text-sm leading-7 text-slate-300">
              Flagged calls, manual reports, and transcript details will appear here once the device starts receiving
              live events from the home setup.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="surface overflow-hidden">
      <div className="hidden grid-cols-[140px_100px_1fr_180px] gap-4 border-b border-white/10 bg-white/[0.03] px-5 py-3 lg:grid">
        <span className="section-label">Trigger</span>
        <span className="section-label">Score</span>
        <span className="section-label">Keywords</span>
        <span className="section-label text-right">Recorded</span>
      </div>

      <div>
        {events.map((event) => (
          <EventRow key={event.id} event={event} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex flex-col gap-4 border-t border-white/10 px-5 py-4 text-sm text-slate-300 sm:flex-row sm:items-center sm:justify-between">
          <span>
            Showing {(page - 1) * limit + 1}-{Math.min(page * limit, total)} of {total}
          </span>
          <div className="flex gap-2">
            {page > 1 && (
              <a href={`?page=${page - 1}`} className="btn-quiet">
                Previous page
              </a>
            )}
            {page < totalPages && (
              <a href={`?page=${page + 1}`} className="btn-quiet">
                Next page
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
