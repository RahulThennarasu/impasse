"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Eye, Search, Users } from "lucide-react";

const publicNegotiations = [
  {
    id: "p1",
    title: "M&A Negotiation Strategy",
    author: "Sarah Chen",
    role: "M&A Director",
    date: "Jan 4, 2026",
    duration: "32m 45s",
    views: 1247,
    score: 94,
    thumbnail: "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=800&h=450&fit=crop",
  },
  {
    id: "p2",
    title: "International Trade Deal",
    author: "Michael Rodriguez",
    role: "Trade Consultant",
    date: "Jan 2, 2026",
    duration: "28m 18s",
    views: 892,
    score: 88,
    thumbnail: "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=800&h=450&fit=crop",
  },
  {
    id: "p3",
    title: "Series A Funding Round",
    author: "Emma Thompson",
    role: "Founder & CEO",
    date: "Dec 30, 2025",
    duration: "24m 56s",
    views: 2103,
    score: 91,
    thumbnail: "https://images.unsplash.com/photo-1553877522-43269d4ea984?w=800&h=450&fit=crop",
  },
  {
    id: "p4",
    title: "Supply Chain Contract",
    author: "James Park",
    role: "Operations Lead",
    date: "Dec 28, 2025",
    duration: "19m 42s",
    views: 654,
    score: 86,
    thumbnail: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&h=450&fit=crop",
  },
  {
    id: "p5",
    title: "Commercial Real Estate",
    author: "Lisa Anderson",
    role: "Real Estate Broker",
    date: "Dec 25, 2025",
    duration: "21m 33s",
    views: 1567,
    score: 89,
    thumbnail: "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&h=450&fit=crop",
  },
  {
    id: "p6",
    title: "Tech Licensing Agreement",
    author: "David Kim",
    role: "Tech Strategist",
    date: "Dec 22, 2025",
    duration: "26m 15s",
    views: 943,
    score: 92,
    thumbnail: "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&h=450&fit=crop",
  },
];

export function LibraryClient() {
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = useMemo(() => {
    const term = searchQuery.toLowerCase();
    return publicNegotiations.filter(
      (neg) => neg.title.toLowerCase().includes(term) || neg.author.toLowerCase().includes(term)
    );
  }, [searchQuery]);

  return (
    <div className="mx-auto max-w-6xl px-6 pb-20 lg:max-w-[1400px]">
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="bg-olive p-[3px] clip-input">
            <div className="relative bg-white px-6 py-4 clip-input">
              <Search size={18} className="absolute left-6 top-1/2 -translate-y-1/2 text-olive" />
              <input
                type="text"
                placeholder="Search by title or author..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className="w-full bg-transparent pl-10 text-sm font-semibold text-ink outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((negotiation, index) => {
          const clipClass = index % 2 === 0 ? "clip-card-a" : "clip-card-b";
          return (
            <div
              key={negotiation.id}
              className={`bg-olive p-[3px] transition hover:-translate-y-1 hover:shadow-xl ${clipClass}`}
            >
              <div className={`overflow-hidden bg-white ${clipClass}`}>
                <div className="relative">
                  <img
                    src={negotiation.thumbnail}
                    alt={negotiation.title}
                    className="h-44 w-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/10 to-transparent" />
                  <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-ink">
                    <Eye size={12} />
                    Watch
                  </div>
                </div>
                <div className="space-y-3 p-6">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-olive">
                    {negotiation.author}
                  </div>
                  <div className="text-lg font-serif text-ink">{negotiation.title}</div>
                  <div className="text-xs text-muted">{negotiation.role}</div>
                  <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-muted">
                    <span>{negotiation.date}</span>
                    <span>•</span>
                    <span>{negotiation.duration}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted">
                    <span className="flex items-center gap-1">
                      <Users size={12} />
                      {negotiation.views} views
                    </span>
                    <span className="rounded-full bg-olive-10 px-3 py-1 text-xs font-semibold text-ink">
                      Score {negotiation.score}
                    </span>
                  </div>
                  <Link
                    href={`/postmortem/${negotiation.id}`}
                    className="inline-flex items-center text-sm font-semibold text-ink"
                  >
                    View highlights
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
