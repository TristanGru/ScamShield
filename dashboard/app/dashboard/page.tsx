import { getSession } from "@auth0/nextjs-auth0";
import { redirect } from "next/navigation";
import { fetchEvents } from "@/lib/api";
import AlertBanner from "@/components/AlertBanner";
import EventTable from "@/components/EventTable";
import StatusBadge from "@/components/StatusBadge";

const LIMIT = 20;

interface PageProps {
  searchParams: { page?: string };
}

/* Shield mark — product identity, not a user avatar */
function ShieldMark() {
  return (
    <svg
      width="36"
      height="36"
      viewBox="0 0 36 36"
      fill="none"
      aria-hidden="true"
      style={{ flexShrink: 0 }}
    >
      <path
        d="M18 3L6 8v9c0 7.18 5.16 13.9 12 15.48C24.84 30.9 30 24.18 30 17V8L18 3z"
        fill="rgba(59,130,246,0.15)"
        stroke="rgba(59,130,246,0.40)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="M13 18l3.5 3.5L23 14"
        stroke="#93c5fd"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default async function DashboardPage({ searchParams }: PageProps) {
  const session = await getSession();
  if (!session) redirect("/api/auth/login");

  const page = parseInt(searchParams.page ?? "1");

  let events: Awaited<ReturnType<typeof fetchEvents>>["events"] = [];
  let total = 0;
  let piError = false;

  try {
    const data = await fetchEvents(page, LIMIT);
    events = data.events;
    total = data.total;
  } catch {
    piError = true;
  }

  const mostRecent = events.length > 0 ? events[0] : null;

  return (
    <main style={{ minHeight: "100vh", paddingBottom: "48px" }}>

      {/* ── Site header ─────────────────────────────────────────────── */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          backgroundColor: "rgba(8,14,24,0.92)",
          borderBottom: "1px solid var(--color-line-subtle)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
        }}
      >
        <div className="shell-wrap">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "16px",
              padding: "14px 0",
              flexWrap: "wrap",
            }}
          >
            {/* Left — product mark + status */}
            <div style={{ display: "flex", alignItems: "center", gap: "20px", flexWrap: "wrap" }}>
              {/* Logo group */}
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <ShieldMark />
                <div>
                  <p
                    style={{
                      fontSize: "11px",
                      fontWeight: 600,
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      color: "var(--color-ink-muted)",
                      lineHeight: 1,
                    }}
                  >
                    Family dashboard
                  </p>
                  <p
                    style={{
                      fontSize: "17px",
                      fontWeight: 700,
                      color: "var(--color-ink-primary)",
                      lineHeight: 1.2,
                      letterSpacing: "-0.01em",
                      marginTop: "3px",
                    }}
                  >
                    ScamShield
                  </p>
                </div>
              </div>

              {/* Live status */}
              <StatusBadge />
            </div>

            {/* Right — account */}
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                className="chip"
                style={{ maxWidth: "220px", overflow: "hidden", textOverflow: "ellipsis" }}
                title={session.user?.email}
              >
                {session.user?.email}
              </span>
              <a href="/api/auth/logout" className="btn-quiet">
                Sign out
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* ── Page body ───────────────────────────────────────────────── */}
      <div className="shell-wrap" style={{ paddingTop: "32px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>

          {/* ── Pi connectivity error ──────────────────────────────── */}
          {piError && (
            <div
              style={{
                padding: "14px 18px",
                backgroundColor: "var(--color-watch-dim)",
                border: "1px solid rgba(245,158,11,0.18)",
                borderRadius: "var(--radius-panel)",
                display: "flex",
                flexDirection: "column",
                gap: "4px",
              }}
              role="alert"
            >
              <p
                style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "var(--color-watch-text)",
                  lineHeight: 1,
                }}
              >
                Device unreachable
              </p>
              <p
                style={{
                  fontSize: "13px",
                  color: "rgba(252,211,77,0.75)",
                  lineHeight: 1.55,
                }}
              >
                ScamShield cannot reach the Raspberry Pi right now. Events will resume once
                the local device and tunnel come back online.
              </p>
            </div>
          )}

          {/* ── Primary alert + legend grid ───────────────────────── */}
          <section
            style={{
              display: "grid",
              gap: "16px",
              gridTemplateColumns: "1fr",
            }}
            className="xl:grid-cols-[1fr_320px]"
            aria-label="Latest alert"
          >
            {/* Alert banner */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <p className="kicker">Latest alert</p>
                {total > 0 && (
                  <span className="chip">{total} recorded</span>
                )}
              </div>
              <AlertBanner event={mostRecent} total={total} />
            </div>

            {/* Legend / how to read */}
            <aside
              className="surface-raised"
              style={{ padding: "20px" }}
              aria-label="How to interpret alerts"
            >
              <p className="kicker" style={{ marginBottom: "16px" }}>Signal guide</p>

              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <p
                  style={{
                    fontSize: "13px",
                    lineHeight: 1.6,
                    color: "var(--color-ink-secondary)",
                  }}
                >
                  Alerts are raised when ScamShield detects scam language on a live call,
                  or when someone presses the device button directly.
                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {/* Safe */}
                  <div
                    style={{
                      borderLeft: "2px solid var(--color-safe)",
                      paddingLeft: "10px",
                    }}
                  >
                    <p className="kicker" style={{ color: "var(--color-safe-text)", marginBottom: "4px" }}>
                      All clear
                    </p>
                    <p style={{ fontSize: "12px", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                      No suspicious activity logged.
                    </p>
                  </div>

                  {/* Watch */}
                  <div
                    style={{
                      borderLeft: "2px solid var(--color-watch)",
                      paddingLeft: "10px",
                    }}
                  >
                    <p className="kicker" style={{ color: "var(--color-watch-text)", marginBottom: "4px" }}>
                      Manual report
                    </p>
                    <p style={{ fontSize: "12px", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                      A resident or caregiver flagged the call directly.
                    </p>
                  </div>

                  {/* Threat */}
                  <div
                    style={{
                      borderLeft: "2px solid var(--color-threat)",
                      paddingLeft: "10px",
                    }}
                  >
                    <p className="kicker" style={{ color: "var(--color-threat-text)", marginBottom: "4px" }}>
                      High confidence scam
                    </p>
                    <p style={{ fontSize: "12px", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                      ScamShield matched suspicious language patterns with high confidence.
                    </p>
                  </div>
                </div>
              </div>
            </aside>
          </section>

          {/* ── Event log ─────────────────────────────────────────── */}
          <section
            style={{ display: "flex", flexDirection: "column", gap: "12px" }}
            aria-label="Event log"
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <p className="kicker">Event log</p>
              {total > 0 && (
                <span
                  style={{
                    fontSize: "12px",
                    color: "var(--color-ink-muted)",
                  }}
                >
                  {total} total
                </span>
              )}
            </div>
            <EventTable events={events} total={total} page={page} limit={LIMIT} />
          </section>

        </div>
      </div>
    </main>
  );
}
