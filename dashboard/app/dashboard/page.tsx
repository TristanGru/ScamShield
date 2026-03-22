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
    <main className="min-h-screen text-slate-100">
      <header className="sticky top-0 z-10 border-b border-sky-950/60 bg-slate-950/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-sm font-semibold text-emerald-200 shadow-[0_0_30px_rgba(74,222,128,0.12)]">
                SS
              </span>
              <div>
                <span className="block text-xl font-semibold tracking-tight text-white">ScamShield</span>
                <span className="block text-xs uppercase tracking-[0.28em] text-slate-500">
                  Family Safety Dashboard
                </span>
              </div>
            </div>
            <StatusBadge />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:justify-end">
            <span className="max-w-full rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-slate-300 shadow-[0_10px_30px_rgba(2,6,23,0.2)]">
              {session.user?.email}
            </span>
            <a
              href="/api/auth/logout"
              className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-slate-200 transition-colors hover:bg-white/10"
            >
              Log out
            </a>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:py-10">
        {piError && (
          <div className="rounded-3xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-sm text-amber-200 shadow-[0_18px_60px_rgba(120,53,15,0.22)]">
            Warning: Cannot reach the Pi. Check that ScamShield is running and the tunnel is active.
          </div>
        )}

        <section>
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
            Latest Alert
          </h2>
          <AlertBanner event={mostRecent} total={total} />
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Event Log
            </h2>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-400">
              {total} total
            </span>
          </div>
          <EventTable events={events} total={total} page={page} limit={LIMIT} />
        </section>
      </div>
    </main>
  );
}
