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
    <div className="border-b border-slate-800 last:border-0">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center gap-4 px-4 py-3 text-left hover:bg-slate-800/50 transition-colors"
      >
        {/* Trigger badge */}
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
            isAuto
              ? "bg-red-900/50 text-red-400"
              : "bg-amber-900/50 text-amber-400"
          }`}
        >
          {isAuto ? "Auto" : "Manual"}
        </span>

        {/* Score */}
        <span className="shrink-0 w-10 text-center text-sm font-bold">
          {event.scam_score != null ? (
            <span className="text-red-400">{event.scam_score}</span>
          ) : (
            <span className="text-slate-500">—</span>
          )}
        </span>

        {/* Keywords */}
        <div className="flex flex-1 flex-wrap gap-1 min-w-0">
          {event.keywords.length > 0 ? (
            event.keywords.slice(0, 4).map((kw) => (
              <span
                key={kw}
                className="rounded bg-slate-700 px-1.5 py-0.5 text-xs text-slate-300"
              >
                {kw}
              </span>
            ))
          ) : (
            <span className="text-xs text-slate-500 italic">No keywords matched</span>
          )}
          {event.keywords.length > 4 && (
            <span className="text-xs text-slate-500">+{event.keywords.length - 4} more</span>
          )}
        </div>

        {/* Date + SMS */}
        <div className="shrink-0 text-right">
          <p className="text-xs text-slate-400">{formatDate(event.created_at)}</p>
          {event.sms_sent === 1 && (
            <p className="text-xs text-green-500">SMS sent ✓</p>
          )}
        </div>

        {/* Expand arrow */}
        <span className="shrink-0 text-slate-500 text-sm">
          {expanded ? "▲" : "▼"}
        </span>
      </button>

      {expanded && (
        <div className="bg-slate-900/60 px-4 py-3 border-t border-slate-800">
          <p className="text-xs text-slate-400 mb-1 font-medium uppercase tracking-wide">
            Transcript
          </p>
          <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
            {event.transcript || "No transcript available."}
          </p>
          <p className="mt-2 text-xs text-slate-600">Event ID: {event.id}</p>
        </div>
      )}
    </div>
  );
}
