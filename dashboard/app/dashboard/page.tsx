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
    <main className="min-h-screen bg-slate-950 text-slate-100">
      {/* Nav */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-white">🛡 ScamShield</span>
            <StatusBadge />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">{session.user?.email}</span>
            <a
              href="/auth/logout"
              className="rounded bg-slate-800 px-3 py-1 text-xs text-slate-300 hover:bg-slate-700 transition-colors"
            >
              Log out
            </a>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-4 py-6 space-y-6">
        {/* Pi offline warning */}
        {piError && (
          <div className="rounded-xl border border-amber-700/50 bg-amber-900/20 px-4 py-3 text-sm text-amber-400">
            ⚠ Cannot reach the Pi. Check that ScamShield is running and the tunnel is active.
          </div>
        )}

        {/* Most recent alert */}
        <section>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
            Latest Alert
          </h2>
          <AlertBanner event={mostRecent} total={total} />
        </section>

        {/* Event log */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500">
              Event Log
            </h2>
            <span className="text-xs text-slate-600">{total} total</span>
          </div>
          <EventTable events={events} total={total} page={page} limit={LIMIT} />
        </section>
      </div>
    </main>
  );
}
