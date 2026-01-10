import Link from "next/link";
import { Play } from "lucide-react";

const mockNegotiations = [
  {
    id: "1",
    title: "Executive Compensation",
    scenario: "Salary Negotiation",
    date: "Jan 5, 2026",
    duration: "18m 32s",
    score: 85,
    thumbnail: "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=800&h=450&fit=crop",
  },
  {
    id: "2",
    title: "Supply Chain Agreement",
    scenario: "Vendor Contract",
    date: "Jan 3, 2026",
    duration: "22m 15s",
    score: 78,
    thumbnail: "https://images.unsplash.com/photo-1556761175-b413da4baf72?w=800&h=450&fit=crop",
  },
  {
    id: "3",
    title: "Strategic Alliance",
    scenario: "Partnership Terms",
    date: "Dec 28, 2025",
    duration: "15m 48s",
    score: 92,
    thumbnail: "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=800&h=450&fit=crop",
  },
  {
    id: "4",
    title: "Commercial Lease",
    scenario: "Real Estate Deal",
    date: "Dec 20, 2025",
    duration: "25m 10s",
    score: 73,
    thumbnail: "https://images.unsplash.com/photo-1560520653-9e0e4c89eb11?w=800&h=450&fit=crop",
  },
];

export function RecentSessions() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-20 lg:max-w-[1400px]">
      <div className="mt-14 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-serif text-[#1a1a1a]">Recent sessions</h2>
          <p className="mt-2 text-sm text-[#666]">Review your latest negotiations.</p>
        </div>
        <Link
          href="/library"
          className="rounded-full border-2 border-black/10 bg-white px-5 py-2 text-sm font-semibold text-[#1a1a1a] transition hover:border-black/20 hover:bg-black/5"
        >
          Explore library
        </Link>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        {mockNegotiations.map((negotiation, index) => {
          const clipClass = index % 2 === 0 ? "clip-card-a" : "clip-card-b";
          return (
            <div key={negotiation.id} className={`bg-[#7fb069] p-[3px] ${clipClass}`}>
              <div className={`overflow-hidden bg-white ${clipClass}`}>
                <div className="relative">
                  <img
                    src={negotiation.thumbnail}
                    alt={negotiation.title}
                    className="h-48 w-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/10 to-transparent" />
                  <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-[#1a1a1a]">
                    <Play size={12} />
                    Replay
                  </div>
                </div>
                <div className="space-y-3 p-6">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[#7fb069]">
                    {negotiation.scenario}
                  </div>
                  <div className="text-xl font-serif text-[#1a1a1a]">{negotiation.title}</div>
                  <div className="flex flex-wrap items-center gap-3 text-xs font-medium text-[#666]">
                    <span>{negotiation.date}</span>
                    <span>•</span>
                    <span>{negotiation.duration}</span>
                    <span>•</span>
                    <span>Score {negotiation.score}</span>
                  </div>
                  <Link
                    href={`/postmortem/${negotiation.id}`}
                    className="inline-flex items-center text-sm font-semibold text-[#1a1a1a]"
                  >
                    View post-mortem
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
