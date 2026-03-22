import type { ScamEvent } from "@/lib/api";

function formatRelative(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minutes ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hours ago`;
  return new Date(isoString).toLocaleDateString();
}

interface AlertBannerProps {
  event: ScamEvent | null;
  total: number;
}

export default function AlertBanner({ event, total }: AlertBannerProps) {
  if (!event) {
    return (
      <div className="surface-strong overflow-hidden">
        <div className="grid gap-0 lg:grid-cols-[220px_1fr]">
          <div className="border-b border-white/10 bg-emerald-500/10 px-5 py-5 lg:border-b-0 lg:border-r">
            <p className="section-label text-emerald-200/80">Status</p>
            <p className="mt-3 text-2xl font-semibold text-emerald-100">All clear</p>
          </div>
          <div className="px-5 py-5">
            <p className="text-sm leading-7 text-slate-200">
              ScamShield is actively listening for suspicious call behavior. New automatic alerts and manual reports
              will appear here as soon as they are recorded.
            </p>
            <p className="mt-4 kicker">{total} alerts currently on file</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="surface-strong overflow-hidden border-rose-400/20">
      <div className="grid gap-0 lg:grid-cols-[220px_1fr_160px]">
        <div className="border-b border-white/10 bg-rose-500/12 px-5 py-5 lg:border-b-0 lg:border-r">
          <p className="section-label text-rose-200/80">Alert State</p>
          <p className="mt-3 text-2xl font-semibold text-rose-100">Scam detected</p>
          <p className="mt-2 text-sm text-rose-100/75">
            {event.trigger_type === "manual" ? "Reported manually on device" : "Raised by live monitoring"}
          </p>
        </div>

        <div className="px-5 py-5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="utility-chip text-xs">{formatRelative(event.created_at)}</span>
            {event.trigger_type === "manual" && <span className="utility-chip text-xs">Manual report</span>}
          </div>
          <p className="mt-4 text-base leading-7 text-slate-100">
            {event.transcript || "No transcript was captured for this event."}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {event.keywords.length > 0 ? (
              event.keywords.map((kw) => (
                <span
                  key={kw}
                  className="rounded-xl border border-rose-200/10 bg-rose-500/10 px-3 py-1 text-xs text-rose-100/90"
                >
                  {kw}
                </span>
              ))
            ) : (
              <span className="text-sm text-slate-400">No keywords matched.</span>
            )}
          </div>
        </div>

        <div className="border-t border-white/10 bg-white/[0.03] px-5 py-5 lg:border-l lg:border-t-0">
          <p className="section-label">Risk score</p>
          <p className="mt-3 text-4xl font-semibold text-white">{event.scam_score ?? "--"}%</p>
          <p className="mt-3 text-sm text-slate-300">
            {total} total alert{total !== 1 ? "s" : ""} logged for this household.
          </p>
        </div>
      </div>
    </div>
  );
}
