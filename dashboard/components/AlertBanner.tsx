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
      <div className="rounded-3xl border border-emerald-400/20 bg-[linear-gradient(135deg,rgba(16,185,129,0.18),rgba(5,46,22,0.18))] p-5 shadow-[0_24px_80px_rgba(6,78,59,0.24)]">
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-emerald-200">All clear</p>
        <p className="mt-2 text-sm leading-6 text-emerald-100/90">
          ScamShield is monitoring for suspicious calls and will alert trusted contacts if something looks wrong.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-red-500/25 bg-[linear-gradient(135deg,rgba(127,29,29,0.5),rgba(69,10,10,0.28))] p-5 shadow-[0_24px_80px_rgba(127,29,29,0.24)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-red-200">Scam Detected</span>
            {event.trigger_type === "manual" && (
              <span className="rounded-full border border-amber-300/10 bg-amber-900/40 px-2 py-0.5 text-xs text-amber-200">
                Manual Report
              </span>
            )}
          </div>
          <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-200">{event.transcript}</p>
          {event.keywords.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {event.keywords.map((kw) => (
                <span
                  key={kw}
                  className="rounded-full border border-red-400/10 bg-red-800/40 px-2 py-0.5 text-xs text-red-100"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="shrink-0 text-right">
          <p className="text-xs uppercase tracking-[0.2em] text-red-200/70">{formatRelative(event.created_at)}</p>
          {event.scam_score != null && (
            <p className="mt-2 text-3xl font-bold text-red-100">{event.scam_score}%</p>
          )}
        </div>
      </div>
      <p className="mt-4 text-xs uppercase tracking-[0.22em] text-red-100/55">
        {total} total alert{total !== 1 ? "s" : ""} logged
      </p>
    </div>
  );
}
