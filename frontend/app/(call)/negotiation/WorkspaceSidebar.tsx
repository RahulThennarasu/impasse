"use client";

import { Button, Disclosure, Tab } from "@headlessui/react";
import { Lightbulb, Minimize2, StickyNote } from "lucide-react";
import type { CoachTip } from "@/lib/api";

type WorkspaceSidebarProps = {
  isSidebarOpen: boolean;
  onClose: () => void;
  coachSuggestions: CoachTip[];
  notes: string;
};

export function WorkspaceSidebar({
  isSidebarOpen,
  onClose,
  coachSuggestions,
  notes,
}: WorkspaceSidebarProps) {
  return (
    <aside
      className={`relative z-40 flex h-full flex-col border-r border-white/10 bg-white/95 text-ink backdrop-blur-3xl transition-all duration-300 ${
        isSidebarOpen ? "w-[420px]" : "w-0"
      }`}
    >
      {isSidebarOpen && (
        <div className="flex h-full flex-col">
          <div className="border-b border-black/10 bg-white px-6 py-5">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-serif text-ink">session workspace</h2>
                <p className="text-xs font-semibold text-muted">Salary Negotiation • Level 3</p>
              </div>
              <Button
                type="button"
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-black/10 text-muted transition hover:bg-black/5 cursor-pointer"
              >
                <Minimize2 size={16} />
              </Button>
            </div>
          </div>

          <Tab.Group>
            <Tab.List className="flex border-b border-black/10 bg-white">
              {[
                { label: "Notes", icon: StickyNote },
                { label: "Coach", icon: Lightbulb },
              ].map((tab) => (
                <Tab
                  key={tab.label}
                  className={({ selected }) =>
                    `flex flex-1 items-center justify-center gap-2 py-3 text-xs font-semibold uppercase tracking-[0.2em] transition cursor-pointer ${
                      selected ? "text-ink" : "text-muted-strong"
                    }`
                  }
                >
                  <tab.icon size={14} />
                  {tab.label}
                </Tab>
              ))}
            </Tab.List>
            <Tab.Panels className="scroll-thin flex-1 overflow-y-auto px-6 py-6">
              <Tab.Panel className="space-y-4">
                <textarea
                  value={notes}
                  readOnly
                  placeholder="Write your notes, anchors, and fallback offers..."
                  className="h-72 w-full resize-none rounded-lg border border-black/10 bg-white p-4 text-sm text-ink outline-none"
                />
                <div className="rounded-lg border border-black/10 bg-subtle p-4 text-sm text-muted">
                  Tip: Keep your opening number 10-15% above your target. Let the opponent come up to you.
                </div>
              </Tab.Panel>
              <Tab.Panel className="space-y-4">
                {coachSuggestions.map((suggestion) => (
                  <Disclosure key={suggestion.id}>
                    {({ open }) => (
                      <div className="rounded-xl border border-black/10 bg-white p-4">
                        <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-[0.2em] text-olive">
                          <span>{suggestion.category}</span>
                          <span className="text-muted-strong">{suggestion.time}</span>
                        </div>
                        <p className={`mt-3 text-sm text-ink ${open ? "" : "coach-blur"}`}>
                          {suggestion.text}
                        </p>
                        <div className="mt-4 flex items-center justify-between">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              suggestion.priority === "high"
                                ? "bg-ink text-white"
                                : suggestion.priority === "medium"
                                ? "bg-black/10 text-ink"
                                : "bg-black/5 text-muted"
                            }`}
                          >
                            {suggestion.priority} priority
                          </span>
                          <Disclosure.Button className="text-xs font-semibold text-ink cursor-pointer">
                            {open ? "Hide" : "Reveal"}
                          </Disclosure.Button>
                        </div>
                      </div>
                    )}
                  </Disclosure>
                ))}
              </Tab.Panel>
            </Tab.Panels>
          </Tab.Group>
        </div>
      )}
    </aside>
  );
}
