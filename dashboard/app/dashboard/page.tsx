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
                <p className="max-w-2xl text-sm leading-6 text-slate-300">
                  A calm monitoring view for families protecting older relatives from suspicious calls at home.
                </p>
              </div>
            </div>
            <StatusBadge />
          </div>

          <div className="flex flex-col items-start gap-3 lg:items-end">
            <div className="utility-chip max-w-full break-all">{session.user?.email}</div>
            <a href="/api/auth/logout" className="btn-quiet">
              Log out
            </a>
          </div>
        </div>
      </header>

      <div className="shell-wrap space-y-8 pt-8">
        {piError && (
          <div className="surface px-5 py-4 text-sm leading-6 text-amber-100">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
              <span className="font-medium text-amber-200">Connection watch</span>
              <span className="kicker text-amber-200/80">Pi currently unreachable</span>
            </div>
            <p className="mt-2 text-amber-100/90">
              ScamShield cannot reach the Raspberry Pi right now. Live events will appear again once the local device
              and tunnel are available.
            </p>
          </div>
        )}

        <section className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h2 className="section-label">Latest Alert</h2>
              <span className="utility-chip text-xs">{total} recorded events</span>
            </div>
            <AlertBanner event={mostRecent} total={total} />
          </div>

          <aside className="surface-strong px-5 py-5">
            <p className="section-label">How To Read This</p>
            <div className="mt-4 space-y-4 text-sm leading-6 text-slate-300">
              <p>
                Automatic alerts come from ScamShield listening for scam language during speakerphone calls. Manual
                alerts come from a physical button press on the device.
              </p>
              <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <div className="border-l border-emerald-500/30 pl-3">
                  <p className="kicker text-emerald-200">Safe signal</p>
                  <p className="mt-1 text-slate-300">No suspicious activity has been logged recently.</p>
                </div>
                <div className="border-l border-amber-400/30 pl-3">
                  <p className="kicker text-amber-200">Manual report</p>
                  <p className="mt-1 text-slate-300">A caregiver or resident flagged the call directly.</p>
                </div>
                <div className="border-l border-rose-400/30 pl-3">
                  <p className="kicker text-rose-200">High score</p>
                  <p className="mt-1 text-slate-300">Stronger scam confidence based on detected language.</p>
                </div>
              </div>
            </div>
          </aside>
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h2 className="section-label">Event Log</h2>
            <span className="kicker">{total} total</span>
          </div>
          <EventTable events={events} total={total} page={page} limit={LIMIT} />
        </section>
      </div>
    </main>
  );
}
