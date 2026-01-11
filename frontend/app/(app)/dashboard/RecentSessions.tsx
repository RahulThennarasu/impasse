"use client";

import Link from "next/link";
import { Play } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchVideoLinks, type VideoLink } from "@/lib/api";

export function RecentSessions() {
  const [sessions, setSessions] = useState<VideoLink[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchVideoLinks(true)
      .then((response) => {
        setSessions(response.videos ?? []);
        setError(null);
      })
      .catch(() => {
        setError("Unable to load recent sessions.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <section className="mx-auto max-w-6xl px-6 pb-20 lg:max-w-[1400px]">
      <div className="mt-14 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-serif text-ink">Recent sessions</h2>
          <p className="mt-2 text-sm text-muted">Review your latest negotiations.</p>
        </div>
        <Link
          href="/library"
          className="rounded-full border-2 border-black/10 bg-white px-5 py-2 text-sm font-semibold text-ink transition hover:border-black/20 hover:bg-black/5"
        >
          Explore library
        </Link>
      </div>

      <div className="mt-8">
        {loading ? (
          <p className="text-sm text-muted">Loading recent sessions...</p>
        ) : error ? (
          <p className="text-sm text-danger-muted">{error}</p>
        ) : sessions.length === 0 ? (
          <p className="text-sm text-muted">No public sessions yet.</p>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            {sessions.map((session, index) => {
              const clipClass = index % 2 === 0 ? "clip-card-a" : "clip-card-b";
              return (
                <div key={session.id} className={`bg-olive p-[3px] ${clipClass}`}>
                  <div className={`overflow-hidden bg-white ${clipClass}`}>
                    <div className="relative">
                      <div className="h-48 w-full bg-gradient-to-br from-olive-10 via-white to-olive-10" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/10 via-black/0 to-transparent" />
                      <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-ink">
                        <Play size={12} />
                        Replay
                      </div>
                    </div>
                    <div className="space-y-3 p-6">
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-olive">
                        Public session {session.id.slice(0, 8)}
                      </div>
                      <div className="text-xl font-serif text-ink">
                        {session.title || (session.link ? "Recording ready" : "Negotiation session")}
                      </div>
                      <div className="flex flex-wrap items-center gap-3 text-xs font-medium text-muted">
                        {session.created_at ? (
                          <span>{new Date(session.created_at).toLocaleString()}</span>
                        ) : (
                          <span>Processing</span>
                        )}
                      </div>
                      <Link
                        href={`/postmortem/${session.id}`}
                        className="inline-flex items-center text-sm font-semibold text-ink"
                      >
                        View post-mortem
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
