"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Eye, Search } from "lucide-react";
import { Tab } from "@headlessui/react";
import { fetchVideoLinks, updateVideoTitle, type VideoLink } from "@/lib/api";

export function LibraryClient() {
  const [searchQuery, setSearchQuery] = useState("");
  const [userSessions, setUserSessions] = useState<VideoLink[]>([]);
  const [userLoading, setUserLoading] = useState(false);
  const [userError, setUserError] = useState<string | null>(null);
  const [publicSessions, setPublicSessions] = useState<VideoLink[]>([]);
  const [publicLoading, setPublicLoading] = useState(false);
  const [publicError, setPublicError] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const term = searchQuery.toLowerCase();
    return publicSessions.filter(
      (session) =>
        session.id.toLowerCase().includes(term) ||
        (session.link ?? "").toLowerCase().includes(term)
    );
  }, [publicSessions, searchQuery]);

  useEffect(() => {
    setUserLoading(true);
    const userId = getUserId();
    fetchVideoLinks(userId)
      .then((response) => {
        setUserSessions(response.videos ?? []);
        setUserError(null);
      })
      .catch(() => {
        setUserError("Unable to load your sessions.");
      })
      .finally(() => {
        setUserLoading(false);
      });
  }, []);

  useEffect(() => {
    setPublicLoading(true);
    fetchVideoLinks(true)
      .then((response) => {
        setPublicSessions(response.videos ?? []);
        setPublicError(null);
      })
      .catch(() => {
        setPublicError("Unable to load public sessions.");
      })
      .finally(() => {
        setPublicLoading(false);
      });
  }, []);

  const handleRename = (session: VideoLink, scope: "public" | "user") => {
    const currentTitle = session.title ?? "";
    const nextTitle = window.prompt("Rename session", currentTitle);
    if (!nextTitle) return;
    updateVideoTitle(session.id, nextTitle.trim())
      .then(() => {
        if (scope === "public") {
          setPublicSessions((prev) =>
            prev.map((item) =>
              item.id === session.id ? { ...item, title: nextTitle.trim() } : item
            )
          );
        } else {
          setUserSessions((prev) =>
            prev.map((item) =>
              item.id === session.id ? { ...item, title: nextTitle.trim() } : item
            )
          );
        }
      })
      .catch(() => {
        window.alert("Unable to rename session.");
      });
  };

  return (
    <div className="mx-auto max-w-6xl px-6 pb-20 lg:max-w-[1400px]">
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="bg-olive p-[3px] clip-input">
            <div className="relative bg-white px-6 py-4 clip-input">
              <Search
                size={18}
                className="absolute left-6 top-1/2 -translate-y-1/2 text-olive"
              />
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

      <Tab.Group>
        <Tab.List className="mt-10 flex items-center gap-3">
          {["Public Sessions", "Your Sessions"].map((label) => (
            <Tab
              key={label}
              className={({ selected }) =>
                `rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] transition cursor-pointer ${
                  selected ? "bg-olive text-white" : "bg-white/80 text-ink"
                }`
              }
            >
              {label}
            </Tab>
          ))}
        </Tab.List>
        <Tab.Panels className="mt-8">
          <Tab.Panel>
            <div className="rounded-2xl border border-white/40 bg-white/70 p-6">
              {publicLoading ? (
                <p className="text-sm text-muted">Loading public sessions...</p>
              ) : publicError ? (
                <p className="text-sm text-danger-muted">{publicError}</p>
              ) : filtered.length === 0 ? (
                <p className="text-sm text-muted">No public sessions yet.</p>
              ) : (
                <div className="grid gap-4">
                  {filtered.map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between rounded-xl border border-black/10 bg-white px-4 py-3"
                    >
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-olive">
                          Public session {session.id.slice(0, 8)}
                        </div>
                        <div className="mt-1 text-sm text-ink">
                          {session.title || (session.link ? "Recording ready" : "Video processing")}
                        </div>
                        {session.created_at ? (
                          <div className="mt-1 text-xs text-muted">
                            {new Date(session.created_at).toLocaleString()}
                          </div>
                        ) : null}
                      </div>
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => handleRename(session, "public")}
                          className="text-xs font-semibold uppercase tracking-[0.18em] text-olive"
                        >
                          Rename
                        </button>
                        <Link
                          href={`/postmortem/${session.id}`}
                          className="inline-flex items-center gap-2 text-sm font-semibold text-ink"
                        >
                          <Eye size={14} />
                          View
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Tab.Panel>
          <Tab.Panel>
            <div className="rounded-2xl border border-white/40 bg-white/70 p-6">
              {userLoading ? (
                <p className="text-sm text-muted">Loading your sessions...</p>
              ) : userError ? (
                <p className="text-sm text-danger-muted">{userError}</p>
              ) : userSessions.length === 0 ? (
                <p className="text-sm text-muted">No sessions yet.</p>
              ) : (
                <div className="grid gap-4">
                  {userSessions.map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between rounded-xl border border-black/10 bg-white px-4 py-3"
                    >
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-olive">
                          Session {session.id.slice(0, 8)}
                        </div>
                        <div className="mt-1 text-sm text-ink">
                          {session.title || (session.link ? "Recording ready" : "Video processing")}
                        </div>
                        {session.created_at ? (
                          <div className="mt-1 text-xs text-muted">
                            {new Date(session.created_at).toLocaleString()}
                          </div>
                        ) : null}
                      </div>
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => handleRename(session, "user")}
                          className="text-xs font-semibold uppercase tracking-[0.18em] text-olive"
                        >
                          Rename
                        </button>
                        <Link
                          href={`/postmortem/${session.id}`}
                          className="text-sm font-semibold text-ink"
                        >
                          View
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}
