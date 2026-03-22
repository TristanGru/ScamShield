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

function ScoreLabel({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <span
        style={{
          fontSize: "18px",
          fontWeight: 600,
          color: "var(--color-ink-muted)",
          lineHeight: 1,
        }}
      >
        —
      </span>
    );
  }

  const color =
    score >= 70
      ? "var(--color-threat-text)"
      : score >= 40
      ? "var(--color-watch-text)"
      : "var(--color-safe-text)";

  return (
    <span
      style={{
        fontSize: "20px",
        fontWeight: 700,
        color,
        lineHeight: 1,
        letterSpacing: "-0.01em",
      }}
      aria-label={`${score} percent confidence`}
    >
      {score}
      <span style={{ fontSize: "11px", fontWeight: 500, color: "var(--color-ink-muted)", marginLeft: "1px" }}>
        %
      </span>
    </span>
  );
}

/* Chevron icon — indicates expand/collapse */
function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      aria-hidden="true"
      style={{
        color: "var(--color-ink-muted)",
        flexShrink: 0,
        transform: open ? "rotate(180deg)" : "rotate(0deg)",
        transition: "transform 180ms ease",
      }}
    >
      <path
        d="M2.5 5L7 9.5L11.5 5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

interface EventRowProps {
  event: ScamEvent;
  onDeleted?: (id: string) => void;
}

export default function EventRow({ event, onDeleted }: EventRowProps) {
  const [expanded, setExpanded] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const isAuto = event.trigger_type === "auto";

  async function handleDelete() {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setDeleting(true);
    try {
      const res = await fetch(`/api/events/${event.id}`, { method: "DELETE" });
      if (res.ok) {
        onDeleted?.(event.id);
      } else {
        setDeleting(false);
        setConfirmDelete(false);
      }
    } catch {
      setDeleting(false);
      setConfirmDelete(false);
    }
  }

  return (
    <div style={{ borderBottom: "1px solid var(--color-line-subtle)" }} className="last:border-b-0">

      {/* ── Collapsed row ──────────────────────────────────────────── */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="interactive-row"
        aria-expanded={expanded}
        aria-label={`${isAuto ? "Automatic" : "Manual"} event, ${event.scam_score !== null ? `${event.scam_score}% confidence` : "no score"}, recorded ${formatDate(event.created_at)}. ${expanded ? "Click to collapse." : "Click to view transcript."}`}
        style={{ padding: "16px 20px" }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "130px 72px 1fr 160px 20px",
            alignItems: "start",
            gap: "16px",
          }}
          className="hidden lg:grid"
        >
          {/* Trigger type */}
          <div>
            <p className="kicker" style={{ marginBottom: "8px" }}>Trigger</p>
            <p
              style={{
                fontSize: "13px",
                fontWeight: 500,
                color: isAuto ? "var(--color-threat-text)" : "var(--color-watch-text)",
                lineHeight: 1,
              }}
            >
              {isAuto ? "Automatic" : "Manual"}
            </p>
          </div>

          {/* Score */}
          <div>
            <p className="kicker" style={{ marginBottom: "8px" }}>Score</p>
            <ScoreLabel score={event.scam_score} />
          </div>

          {/* Keywords */}
          <div>
            <p className="kicker" style={{ marginBottom: "8px" }}>Keywords</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "5px" }}>
              {event.keywords.length > 0 ? (
                <>
                  {event.keywords.slice(0, 5).map((kw) => (
                    <span key={kw} className={`tag ${isAuto ? "tag-threat" : ""}`}>
                      {kw}
                    </span>
                  ))}
                  {event.keywords.length > 5 && (
                    <span
                      style={{
                        fontSize: "11px",
                        color: "var(--color-ink-muted)",
                        lineHeight: 1,
                        paddingTop: "3px",
                      }}
                    >
                      +{event.keywords.length - 5}
                    </span>
                  )}
                </>
              ) : (
                <span style={{ fontSize: "13px", color: "var(--color-ink-muted)" }}>
                  None matched
                </span>
              )}
            </div>
          </div>

          {/* Time + notification */}
          <div style={{ textAlign: "right" }}>
            <p className="kicker" style={{ marginBottom: "8px", textAlign: "right" }}>Recorded</p>
            <p style={{ fontSize: "13px", color: "var(--color-ink-secondary)", lineHeight: 1 }}>
              {formatDate(event.created_at)}
            </p>
            {event.sms_sent === 1 && (
              <p
                style={{
                  marginTop: "5px",
                  fontSize: "11px",
                  color: "var(--color-safe-text)",
                  lineHeight: 1,
                }}
              >
                Family notified
              </p>
            )}
          </div>

          {/* Expand affordance */}
          <div style={{ paddingTop: "20px", display: "flex", justifyContent: "flex-end" }}>
            <Chevron open={expanded} />
          </div>
        </div>

        {/* ── Mobile layout ────────────────────────────────────────── */}
        <div className="flex flex-col gap-3 lg:hidden">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <p
                style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  color: isAuto ? "var(--color-threat-text)" : "var(--color-watch-text)",
                  lineHeight: 1,
                }}
              >
                {isAuto ? "Automatic detection" : "Manual report"}
              </p>
              <p style={{ fontSize: "12px", color: "var(--color-ink-muted)", lineHeight: 1 }}>
                {formatDate(event.created_at)}
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <ScoreLabel score={event.scam_score} />
              <Chevron open={expanded} />
            </div>
          </div>

          {event.keywords.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "5px" }}>
              {event.keywords.slice(0, 4).map((kw) => (
                <span key={kw} className={`tag ${isAuto ? "tag-threat" : ""}`}>
                  {kw}
                </span>
              ))}
              {event.keywords.length > 4 && (
                <span style={{ fontSize: "11px", color: "var(--color-ink-muted)", paddingTop: "3px" }}>
                  +{event.keywords.length - 4}
                </span>
              )}
            </div>
          )}
        </div>
      </button>

      {/* ── Expanded transcript panel ─────────────────────────────── */}
      {expanded && (
        <div
          style={{
            borderTop: "1px solid var(--color-line-subtle)",
            backgroundColor: "rgba(255,255,255,0.015)",
            padding: "20px",
          }}
        >
          <p className="kicker" style={{ marginBottom: "10px" }}>Transcript</p>
          <p
            style={{
              fontSize: "14px",
              lineHeight: 1.7,
              color: "var(--color-ink-secondary)",
              whiteSpace: "pre-wrap",
              maxWidth: "72ch",
            }}
          >
            {event.transcript || "No transcript was captured for this event."}
          </p>
          <div
            style={{
              marginTop: "20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <p
              style={{
                fontSize: "11px",
                color: "var(--color-ink-muted)",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              ID: {event.id}
            </p>

            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              {confirmDelete && !deleting && (
                <span style={{ fontSize: "12px", color: "var(--color-threat-text)" }}>
                  Delete this event?
                </span>
              )}
              {confirmDelete && !deleting && (
                <button
                  onClick={() => setConfirmDelete(false)}
                  style={{
                    fontSize: "12px",
                    color: "var(--color-ink-muted)",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: "4px 8px",
                  }}
                >
                  Cancel
                </button>
              )}
              <button
                onClick={handleDelete}
                disabled={deleting}
                aria-label={confirmDelete ? "Confirm delete event" : "Delete event"}
                style={{
                  fontSize: "12px",
                  fontWeight: 500,
                  color: confirmDelete ? "var(--color-threat-text)" : "var(--color-ink-muted)",
                  background: "none",
                  border: confirmDelete ? "1px solid var(--color-threat-text)" : "1px solid var(--color-line-subtle)",
                  borderRadius: "2px",
                  cursor: deleting ? "not-allowed" : "pointer",
                  padding: "4px 10px",
                  opacity: deleting ? 0.5 : 1,
                  transition: "all 150ms ease",
                }}
              >
                {deleting ? "Deleting…" : confirmDelete ? "Confirm" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
