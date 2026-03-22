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

function AfterShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen pb-12">
      <header className="border-b border-white/5 bg-[rgba(8,17,29,0.88)] backdrop-blur">
        <div className="shell-wrap flex flex-col gap-5 py-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex flex-col gap-4">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-500/20 bg-emerald-500/10 text-base font-semibold text-emerald-200">
                SS
              </div>
              <div className="space-y-2">
                <div>
                  <p className="section-label">Trusted Family View</p>
                  <h1 className="text-3xl font-semibold tracking-tight text-white">ScamShield</h1>
                </div>
                <p className="max-w-2xl text-sm leading-6 text-slate-300">{subtitle}</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <div className="status-chip status-chip--online">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-300" />
                Listening now
              </div>
              <div className="utility-chip text-xs">Nest speaker connected</div>
              <div className="utility-chip text-xs">Last alert 4m ago</div>
            </div>
          </div>

          <div className="flex flex-col items-start gap-3 lg:items-end">
            <div className="utility-chip max-w-full break-all">caregiver@example.com</div>
            <span className="btn-quiet">Log out</span>
          </div>
        </div>
      </header>

      <div className="shell-wrap space-y-8 pt-8">
        <div className="flex items-center justify-between gap-3">
          <h2 className="section-label">{title}</h2>
          <span className="kicker">Review preview</span>
        </div>
        {children}
      </div>
    </main>
  );
}

function AfterEmptyState() {
  return (
    <AfterShell
      title="Empty Household State"
      subtitle="A calm monitoring view for families protecting older relatives from suspicious calls at home."
    >
      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h2 className="section-label">Latest Alert</h2>
            <span className="utility-chip text-xs">0 recorded events</span>
          </div>
          <AlertBanner event={null} total={0} />
        </div>

        <aside className="surface-strong px-5 py-5">
          <p className="section-label">How To Read This</p>
          <div className="mt-4 space-y-4 text-sm leading-6 text-slate-300">
            <p>
              Automatic alerts come from ScamShield listening for scam language during speakerphone calls. Manual
              alerts come from a physical button press on the device.
            </p>
            <div className="grid gap-3">
              <div className="border-l border-emerald-500/30 pl-3">
                <p className="kicker text-emerald-200">Safe signal</p>
                <p className="mt-1 text-slate-300">No suspicious activity has been logged recently.</p>
              </div>
            </div>
          </div>
        </aside>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="section-label">Event Log</h2>
          <span className="kicker">0 total</span>
        </div>
        <EventTable events={[]} total={0} page={1} limit={20} />
      </section>
    </AfterShell>
  );
}

function AfterPopulatedState() {
  return (
    <AfterShell
      title="Active Household State"
      subtitle="A household safety console showing the latest risk signal and the surrounding call history."
    >
      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h2 className="section-label">Latest Alert</h2>
            <span className="utility-chip text-xs">2 recorded events</span>
          </div>
          <AlertBanner event={demoEvent} total={2} />
        </div>

        <aside className="surface-strong px-5 py-5">
          <p className="section-label">How To Read This</p>
          <div className="mt-4 space-y-4 text-sm leading-6 text-slate-300">
            <div className="border-l border-rose-400/30 pl-3">
              <p className="kicker text-rose-200">High score</p>
              <p className="mt-1 text-slate-300">Stronger scam confidence based on detected language.</p>
            </div>
            <div className="border-l border-amber-400/30 pl-3">
              <p className="kicker text-amber-200">Manual report</p>
              <p className="mt-1 text-slate-300">A caregiver or resident flagged the call directly.</p>
            </div>
          </div>
        </aside>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="section-label">Event Log</h2>
          <span className="kicker">2 total</span>
        </div>
        <EventTable events={demoEvents} total={2} page={1} limit={20} />
      </section>
    </AfterShell>
  );
}

export function ReviewComparison({ state }: { state: "empty" | "active" }) {
  return (
    <main className="min-h-screen bg-[var(--bg-canvas)] px-6 py-8 text-white">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <p className="section-label">Design Review</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">ScamShield before and after</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
            Internal review harness for capturing redesign evidence with stable mock data. Existing app routes and
            business logic are unchanged.
          </p>
        </div>

        <div className="grid gap-8 xl:grid-cols-2">
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="section-label">Before</h2>
              <span className="kicker">origin/main baseline</span>
            </div>
            <div className="overflow-hidden rounded-[28px] border border-white/10">
              {state === "empty" ? <BeforeEmptyState /> : <BeforePopulatedState />}
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="section-label">After</h2>
              <span className="kicker">redesigned system</span>
            </div>
            <div className="overflow-hidden rounded-[28px] border border-white/10">
              {state === "empty" ? <AfterEmptyState /> : <AfterPopulatedState />}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
