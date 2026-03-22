"use client";

import { useState } from "react";
import type { ScamEvent } from "@/lib/api";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface EventRowProps {
  event: ScamEvent;
}

export default function EventRow({ event }: EventRowProps) {
  const [expanded, setExpanded] = useState(false);
  const isAuto = event.trigger_type === "auto";

  return (
    <div className="border-b border-white/10 last:border-b-0">
      <button
        onClick={() => setExpanded((value) => !value)}
        className="interactive-row w-full px-4 py-4 text-left transition-colors hover:bg-white/[0.03] sm:px-5"
        aria-expanded={expanded}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex min-w-0 flex-1 flex-col gap-4 lg:flex-row lg:items-start">
            <div className="min-w-[128px]">
              <p className="kicker">Trigger</p>
              <p className={`mt-2 text-sm font-medium ${isAuto ? "text-rose-200" : "text-amber-200"}`}>
                {isAuto ? "Automatic detection" : "Manual report"}
              </p>
            </div>

            <div className="min-w-[84px]">
              <p className="kicker">Score</p>
              <p className="mt-2 text-2xl font-semibold text-white">{event.scam_score ?? "--"}</p>
            </div>

            <div className="min-w-0 flex-1">
              <p className="kicker">Keywords</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {event.keywords.length > 0 ? (
                  event.keywords.slice(0, 5).map((kw) => (
                    <span
                      key={kw}
                      className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-slate-200"
                    >
                      {kw}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-slate-400">No keywords matched.</span>
                )}
                {event.keywords.length > 5 && (
                  <span className="text-xs text-slate-500">+{event.keywords.length - 5} more</span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-end justify-between gap-4 lg:min-w-[180px] lg:flex-col lg:items-end">
            <div>
              <p className="kicker">Recorded</p>
              <p className="mt-2 text-sm text-slate-200">{formatDate(event.created_at)}</p>
              {event.sms_sent === 1 && <p className="mt-1 text-xs text-emerald-300">Trusted contact notified</p>}
            </div>
            <span className="text-sm text-slate-400">{expanded ? "Hide details" : "View details"}</span>
          </div>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/10 bg-white/[0.025] px-4 py-4 sm:px-5">
          <p className="kicker">Transcript</p>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-200">
            {event.transcript || "No transcript available."}
          </p>
          <p className="mt-4 text-xs text-slate-500">Event ID: {event.id}</p>
        </div>
      )}
    </div>
  );
}
