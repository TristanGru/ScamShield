import type { ScamEvent } from "@/lib/api";

function formatRelative(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return new Date(isoString).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function ScoreBar({ score }: { score: number }) {
  // Visual confidence bar — splits at thirds for risk communication
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct >= 70
      ? "var(--color-threat)"
      : pct >= 40
      ? "var(--color-watch)"
      : "var(--color-safe)";

  return (
    <div aria-hidden="true" style={{ marginTop: "10px" }}>
      <div
        style={{
          height: "3px",
          borderRadius: "2px",
          backgroundColor: "rgba(255,255,255,0.07)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            backgroundColor: color,
            transition: "width 300ms ease",
          }}
        />
      </div>
    </div>
  );
}

interface AlertBannerProps {
  event: ScamEvent | null;
  total: number;
}

/* ── All-clear state ────────────────────────────────────────────────── */
function AllClearBanner({ total }: { total: number }) {
  return (
    <div
      className="surface"
      style={{
        overflow: "hidden",
        borderColor: "rgba(34,197,94,0.14)",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "180px 1fr",
        }}
        className="block sm:grid"
      >
        {/* Left — status label */}
        <div
          style={{
            padding: "20px",
            borderRight: "1px solid var(--color-line-subtle)",
            backgroundColor: "var(--color-safe-dim)",
          }}
        >
          <p className="kicker" style={{ color: "var(--color-safe-text)", opacity: 0.7 }}>
            Current status
          </p>
          <p
            style={{
              marginTop: "12px",
              fontSize: "20px",
              fontWeight: 600,
              color: "var(--color-safe-text)",
              lineHeight: 1.2,
            }}
          >
            All clear
          </p>
        </div>

        {/* Right — context */}
        <div style={{ padding: "20px" }}>
          <p
            style={{
              fontSize: "14px",
              lineHeight: 1.6,
              color: "var(--color-ink-secondary)",
            }}
          >
            ScamShield is actively listening for suspicious call behavior. New automatic
            alerts and manual reports will appear here immediately.
          </p>
          {total > 0 && (
            <p
              className="kicker"
              style={{ marginTop: "12px", color: "var(--color-ink-muted)" }}
            >
              {total} alert{total !== 1 ? "s" : ""} on file
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Scam detected state ────────────────────────────────────────────── */
function ScamDetectedBanner({ event, total }: { event: ScamEvent; total: number }) {
  const score = event.scam_score ?? null;
  const isManual = event.trigger_type === "manual";

  return (
    <div
      className="surface"
      style={{
        overflow: "hidden",
        borderColor: "rgba(239,68,68,0.18)",
      }}
      role="alert"
      aria-live="assertive"
    >
      {/* Top bar — severity stripe */}
      <div
        style={{
          height: "3px",
          backgroundColor:
            score !== null && score >= 70
              ? "var(--color-threat)"
              : "var(--color-watch)",
        }}
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "180px 1fr 140px",
        }}
        className="block sm:grid"
      >
        {/* Column 1 — alert state */}
        <div
          style={{
            padding: "20px",
            borderRight: "1px solid var(--color-line-subtle)",
            backgroundColor: "var(--color-threat-dim)",
          }}
        >
          <p className="kicker" style={{ color: "var(--color-threat-text)", opacity: 0.7 }}>
            Alert state
          </p>
          <p
            style={{
              marginTop: "12px",
              fontSize: "18px",
              fontWeight: 600,
              color: "var(--color-threat-text)",
              lineHeight: 1.25,
            }}
          >
            Scam detected
          </p>
          <p
            style={{
              marginTop: "6px",
              fontSize: "12px",
              color: "rgba(252,165,165,0.65)",
              lineHeight: 1.4,
            }}
          >
            {isManual ? "Reported on device" : "Automatic detection"}
          </p>
        </div>

        {/* Column 2 — transcript + keywords */}
        <div style={{ padding: "20px" }}>
          {/* Meta row */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span className="chip">{formatRelative(event.created_at)}</span>
            {isManual && <span className="chip">Manual report</span>}
            {event.sms_sent === 1 && (
              <span
                className="chip"
                style={{
                  color: "var(--color-safe-text)",
                  borderColor: "rgba(34,197,94,0.18)",
                  backgroundColor: "var(--color-safe-dim)",
                }}
              >
                Family notified
              </span>
            )}
          </div>

          {/* Transcript */}
          <p
            style={{
              marginTop: "14px",
              fontSize: "14px",
              lineHeight: 1.65,
              color: "var(--color-ink-primary)",
            }}
          >
            {event.transcript || "No transcript captured for this event."}
          </p>

          {/* Keywords */}
          {event.keywords.length > 0 && (
            <div style={{ marginTop: "12px", display: "flex", flexWrap: "wrap", gap: "6px" }}>
              {event.keywords.map((kw) => (
                <span key={kw} className="tag tag-threat">
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Column 3 — score */}
        <div
          style={{
            padding: "20px",
            borderLeft: "1px solid var(--color-line-subtle)",
          }}
        >
          <p className="kicker">Risk score</p>

          {score !== null ? (
            <>
              <p
                style={{
                  marginTop: "10px",
                  fontSize: "36px",
                  fontWeight: 700,
                  color:
                    score >= 70
                      ? "var(--color-threat-text)"
                      : score >= 40
                      ? "var(--color-watch-text)"
                      : "var(--color-safe-text)",
                  lineHeight: 1,
                  letterSpacing: "-0.02em",
                }}
                aria-label={`Risk score: ${score} percent`}
              >
                {score}
                <span
                  style={{
                    fontSize: "16px",
                    fontWeight: 500,
                    color: "var(--color-ink-muted)",
                    marginLeft: "2px",
                  }}
                >
                  %
                </span>
              </p>
              <ScoreBar score={score} />
            </>
          ) : (
            <p
              style={{
                marginTop: "10px",
                fontSize: "28px",
                fontWeight: 600,
                color: "var(--color-ink-muted)",
              }}
            >
              —
            </p>
          )}

          <p
            style={{
              marginTop: "14px",
              fontSize: "12px",
              color: "var(--color-ink-muted)",
              lineHeight: 1.5,
            }}
          >
            {total} total alert{total !== 1 ? "s" : ""} logged
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AlertBanner({ event, total }: AlertBannerProps) {
  if (!event) {
    return <AllClearBanner total={total} />;
  }
  return <ScamDetectedBanner event={event} total={total} />;
}
