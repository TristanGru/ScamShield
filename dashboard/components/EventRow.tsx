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
        className="flex w-full flex-col gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-800/50 sm:flex-row sm:items-center sm:gap-4"
      >
        <span
          className={`shrink-0 self-start rounded-full px-2 py-0.5 text-xs font-medium ${
            isAuto ? "bg-red-900/50 text-red-400" : "bg-amber-900/50 text-amber-400"
          }`}
        >
          {isAuto ? "Auto" : "Manual"}
        </span>

        <div className="flex w-full items-start justify-between gap-3 sm:w-auto sm:flex-1 sm:items-center">
          <div className="flex min-w-0 flex-1 flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
            <span className="text-xs uppercase tracking-wide text-slate-500 sm:hidden">Score</span>
            <span className="w-10 shrink-0 text-left text-sm font-bold sm:text-center">
          {event.scam_score != null ? (
            <span className="text-red-400">{event.scam_score}</span>
          ) : (
            <span className="text-slate-500">-</span>
          )}
            </span>

            <div className="min-w-0 flex-1">
              <span className="text-xs uppercase tracking-wide text-slate-500 sm:hidden">Keywords</span>
              <div className="mt-1 flex flex-wrap gap-1 sm:mt-0">
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
                  <span className="text-xs italic text-slate-500">No keywords matched</span>
                )}
                {event.keywords.length > 4 && (
                  <span className="text-xs text-slate-500">+{event.keywords.length - 4} more</span>
                )}
              </div>
            </div>
          </div>

          <div className="shrink-0 text-right">
            <span className="text-xs uppercase tracking-wide text-slate-500 sm:hidden">Time</span>
            <p className="mt-1 text-xs text-slate-400 sm:mt-0">{formatDate(event.created_at)}</p>
            {event.sms_sent === 1 && <p className="text-xs text-green-500">SMS sent</p>}
          </div>
        </div>

        <span className="shrink-0 self-end text-sm text-slate-500 sm:self-auto">{expanded ? "^" : "v"}</span>
      </button>

      {expanded && (
        <div className="border-t border-slate-800 bg-slate-900/60 px-4 py-3">
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">
            Transcript
          </p>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
            {event.transcript || "No transcript available."}
          </p>
          <p className="mt-2 text-xs text-slate-600">Event ID: {event.id}</p>
        </div>
      )}
    </div>
  );
}
