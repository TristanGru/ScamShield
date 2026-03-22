import AlertBanner from "@/components/AlertBanner";
import EventTable from "@/components/EventTable";
import type { ScamEvent } from "@/lib/api";

const demoEvent: ScamEvent = {
  id: "demo-event-001",
  created_at: "2026-03-21T14:12:00.000Z",
  trigger_type: "auto",
  scam_score: 92,
  keywords: ["gift card", "urgent", "bank verification"],
  transcript:
    "This is your bank's fraud department. Do not hang up. We need you to move funds immediately and confirm with gift cards.",
  sms_sent: 1,
  synced: 1,
};

const demoEvents: ScamEvent[] = [
  demoEvent,
  {
    id: "demo-event-002",
    created_at: "2026-03-21T10:04:00.000Z",
    trigger_type: "manual",
    scam_score: null,
    keywords: [],
    transcript: "Resident pressed the device button after feeling pressured by the caller.",
    sms_sent: 1,
    synced: 1,
  },
];

/* ── Before snapshot — original baseline ──────────────────────────────── */
function BeforeBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-red-900/40 px-3 py-1 text-xs text-red-400">
      <span className="h-2 w-2 rounded-full bg-red-500" />
      Pi Offline
    </span>
  );
}

function BeforeEmptyState() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-white">ScamShield</span>
            <BeforeBadge />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">caregiver@example.com</span>
            <span className="rounded bg-slate-800 px-3 py-1 text-xs text-slate-300">Log out</span>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-6">
        <div className="rounded-xl border border-amber-700/50 bg-amber-900/20 px-4 py-3 text-sm text-amber-400">
          Warning: Cannot reach the Pi. Check that ScamShield is running and the tunnel is active.
        </div>

        <section>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">Latest Alert</h2>
          <div className="rounded-xl border border-green-800/40 bg-green-900/20 p-4">
            <p className="text-sm text-green-400">No alerts detected. System is monitoring.</p>
          </div>
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500">Event Log</h2>
            <span className="text-xs text-slate-600">0 total</span>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-8 text-center">
            <p className="text-slate-400">No events logged yet.</p>
            <p className="mt-1 text-sm text-slate-600">
              Events will appear here when ScamShield detects a suspicious call.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

function BeforePopulatedState() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-white">ScamShield</span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-green-900/40 px-3 py-1 text-xs text-green-400">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              Listening
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">caregiver@example.com</span>
            <span className="rounded bg-slate-800 px-3 py-1 text-xs text-slate-300">Log out</span>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-6">
        <section>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">Latest Alert</h2>
          <div className="rounded-xl border border-red-700/60 bg-red-900/20 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-red-400">Scam Detected</span>
                </div>
                <p className="mt-1 line-clamp-2 text-sm text-slate-300">{demoEvent.transcript}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {demoEvent.keywords.map((kw) => (
                    <span key={kw} className="rounded-full bg-red-800/50 px-2 py-0.5 text-xs text-red-300">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
              <div className="shrink-0 text-right">
                <p className="text-xs text-slate-400">just now</p>
                <p className="mt-1 text-2xl font-bold text-red-400">92%</p>
              </div>
            </div>
            <p className="mt-3 text-xs text-slate-500">2 total alerts logged</p>
          </div>
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500">Event Log</h2>
            <span className="text-xs text-slate-600">2 total</span>
          </div>
          <div className="flex items-center gap-4 border-b border-slate-800 px-4 py-2 text-xs uppercase tracking-wide text-slate-500">
            <span className="w-16">Type</span>
            <span className="w-10 text-center">Score</span>
            <span className="flex-1">Keywords</span>
            <span className="w-32 text-right">Time</span>
          </div>
          <div className="rounded-b-xl border border-t-0 border-slate-800 bg-slate-900/50">
            {demoEvents.map((event) => (
              <div key={event.id} className="border-b border-slate-800 px-4 py-3 last:border-b-0">
                <div className="flex items-center gap-4">
                  <span className="w-16 rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                    {event.trigger_type}
                  </span>
                  <span className="w-10 text-center text-sm font-bold text-red-400">{event.scam_score ?? "-"}</span>
                  <div className="flex flex-1 flex-wrap gap-1">
                    {event.keywords.length > 0 ? (
                      event.keywords.map((kw) => (
                        <span key={kw} className="rounded bg-slate-700 px-1.5 py-0.5 text-xs text-slate-300">
                          {kw}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">No keywords matched</span>
                    )}
                  </div>
                  <span className="w-32 text-right text-xs text-slate-400">{event.created_at.slice(11, 16)}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

/* ── After shell — uses the new design system ─────────────────────────── */
function ShieldMark() {
  return (
    <svg width="32" height="32" viewBox="0 0 36 36" fill="none" aria-hidden="true" style={{ flexShrink: 0 }}>
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

function AfterShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <main style={{ minHeight: "100vh", paddingBottom: "48px" }}>
      <header
        style={{
          backgroundColor: "rgba(8,14,24,0.92)",
          borderBottom: "1px solid var(--color-line-subtle)",
          backdropFilter: "blur(12px)",
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
            <div style={{ display: "flex", alignItems: "center", gap: "20px", flexWrap: "wrap" }}>
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
              <div className="status-pill status-pill--online">
                <span className="status-dot status-dot--online" />
                Listening now
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span className="chip">caregiver@example.com</span>
              <span className="btn-quiet">Sign out</span>
            </div>
          </div>
        </div>
      </header>

      <div className="shell-wrap" style={{ paddingTop: "32px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <p className="kicker">{title}</p>
            <span className="chip">Review preview</span>
          </div>
          {children}
        </div>
      </div>
    </main>
  );
}

function AfterEmptyState() {
  return (
    <AfterShell title="Empty household state">
      <section
        style={{ display: "grid", gap: "16px" }}
        className="xl:grid-cols-[1fr_320px]"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <p className="kicker">Latest alert</p>
          </div>
          <AlertBanner event={null} total={0} />
        </div>

        <aside className="surface-raised" style={{ padding: "20px" }}>
          <p className="kicker" style={{ marginBottom: "16px" }}>Signal guide</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ borderLeft: "2px solid var(--color-safe)", paddingLeft: "10px" }}>
              <p className="kicker" style={{ color: "var(--color-safe-text)", marginBottom: "4px" }}>All clear</p>
              <p style={{ fontSize: "12px", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                No suspicious activity logged.
              </p>
            </div>
          </div>
        </aside>
      </section>

      <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <p className="kicker">Event log</p>
        <EventTable events={[]} total={0} page={1} limit={20} />
      </section>
    </AfterShell>
  );
}

function AfterPopulatedState() {
  return (
    <AfterShell title="Active household state">
      <section
        style={{ display: "grid", gap: "16px" }}
        className="xl:grid-cols-[1fr_320px]"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <p className="kicker">Latest alert</p>
            <span className="chip">2 recorded</span>
          </div>
          <AlertBanner event={demoEvent} total={2} />
        </div>

        <aside className="surface-raised" style={{ padding: "20px" }}>
          <p className="kicker" style={{ marginBottom: "16px" }}>Signal guide</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ borderLeft: "2px solid var(--color-threat)", paddingLeft: "10px" }}>
              <p className="kicker" style={{ color: "var(--color-threat-text)", marginBottom: "4px" }}>
                High confidence scam
              </p>
              <p style={{ fontSize: "12px", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                ScamShield matched suspicious language with high confidence.
              </p>
            </div>
            <div style={{ borderLeft: "2px solid var(--color-watch)", paddingLeft: "10px" }}>
              <p className="kicker" style={{ color: "var(--color-watch-text)", marginBottom: "4px" }}>
                Manual report
              </p>
              <p style={{ fontSize: "12px", color: "var(--color-ink-muted)", lineHeight: 1.5 }}>
                A resident or caregiver flagged the call directly.
              </p>
            </div>
          </div>
        </aside>
      </section>

      <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <p className="kicker">Event log</p>
          <span style={{ fontSize: "12px", color: "var(--color-ink-muted)" }}>2 total</span>
        </div>
        <EventTable events={demoEvents} total={2} page={1} limit={20} />
      </section>
    </AfterShell>
  );
}

export function ReviewComparison({ state }: { state: "empty" | "active" }) {
  return (
    <main style={{ minHeight: "100vh", backgroundColor: "var(--color-canvas)", padding: "32px 24px" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
        <div>
          <p className="kicker" style={{ marginBottom: "8px" }}>Design review</p>
          <h1
            style={{
              fontSize: "22px",
              fontWeight: 600,
              letterSpacing: "-0.02em",
              color: "var(--color-ink-primary)",
              lineHeight: 1.2,
              margin: 0,
            }}
          >
            ScamShield — before and after
          </h1>
          <p
            style={{
              marginTop: "8px",
              maxWidth: "600px",
              fontSize: "14px",
              lineHeight: 1.6,
              color: "var(--color-ink-secondary)",
            }}
          >
            Internal review harness using stable mock data. App routes and business logic unchanged.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gap: "24px",
          }}
          className="xl:grid-cols-2"
        >
          <section style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <p className="kicker">Before</p>
              <span className="chip">origin/main baseline</span>
            </div>
            <div
              style={{
                overflow: "hidden",
                borderRadius: "6px",
                border: "1px solid var(--color-line-subtle)",
              }}
            >
              {state === "empty" ? <BeforeEmptyState /> : <BeforePopulatedState />}
            </div>
          </section>

          <section style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <p className="kicker">After</p>
              <span className="chip">redesigned system</span>
            </div>
            <div
              style={{
                overflow: "hidden",
                borderRadius: "6px",
                border: "1px solid var(--color-line-subtle)",
              }}
            >
              {state === "empty" ? <AfterEmptyState /> : <AfterPopulatedState />}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
