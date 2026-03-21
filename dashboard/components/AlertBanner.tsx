import type { ScamEvent } from "@/lib/api";

function formatRelative(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return new Date(isoString).toLocaleDateString();
}

interface AlertBannerProps {
  event: ScamEvent | null;
  total: number;
}

export default function AlertBanner({ event, total }: AlertBannerProps) {
  if (!event) {
    return (
      <div className="rounded-xl border border-green-800/40 bg-green-900/20 p-4">
        <p className="text-sm text-green-400">✓ No alerts detected. System is monitoring.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-red-700/60 bg-red-900/20 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-red-400">⚠ Scam Detected</span>
            {event.trigger_type === "manual" && (
              <span className="rounded-full bg-amber-900/50 px-2 py-0.5 text-xs text-amber-400">
                Manual Report
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-slate-300 line-clamp-2">{event.transcript}</p>
          {event.keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {event.keywords.map((kw) => (
                <span
                  key={kw}
                  className="rounded-full bg-red-800/50 px-2 py-0.5 text-xs text-red-300"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="shrink-0 text-right">
          <p className="text-xs text-slate-400">{formatRelative(event.created_at)}</p>
          {event.scam_score != null && (
            <p className="mt-1 text-2xl font-bold text-red-400">{event.scam_score}%</p>
          )}
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-500">
        {total} total alert{total !== 1 ? "s" : ""} logged
      </p>
    </div>
  );
}
