"use client";

import { Button, Disclosure, Tab } from "@headlessui/react";
import { Clock, Lightbulb, Minimize2, StickyNote, TrendingUp } from "lucide-react";

type KeyPoint = {
  label: string;
  value: string;
  trend: "up" | "neutral";
};

type CoachSuggestion = {
  id: number;
  text: string;
  time: string;
  priority: "high" | "medium";
  category: string;
};

type WorkspaceSidebarProps = {
  isSidebarOpen: boolean;
  onClose: () => void;
  keyPoints: KeyPoint[];
  coachSuggestions: CoachSuggestion[];
  notes: string;
  onNotesChange: (value: string) => void;
};

export function WorkspaceSidebar({
  isSidebarOpen,
  onClose,
  keyPoints,
  coachSuggestions,
  notes,
  onNotesChange,
}: WorkspaceSidebarProps) {
  return (
    <aside
      className={`relative z-40 flex h-full flex-col border-r border-white/10 bg-white/95 text-[#1a1a1a] backdrop-blur-3xl transition-all duration-300 ${
        isSidebarOpen ? "w-[420px]" : "w-0"
      }`}
    >
      {isSidebarOpen && (
        <div className="flex h-full flex-col">
          <div className="border-b border-black/10 bg-white px-6 py-5">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-serif text-[#1a1a1a]">session workspace</h2>
                <p className="text-xs font-semibold text-[#666]">Salary Negotiation • Level 3</p>
              </div>
              <Button
                type="button"
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-black/10 text-[#666] transition hover:bg-black/5 cursor-pointer"
              >
                <Minimize2 size={16} />
              </Button>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-3">
              {keyPoints.map((point) => (
                <div key={point.label} className="rounded-lg border border-black/5 bg-black/5 p-3">
                  <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#666]">
                    {point.label}
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-sm font-bold text-[#1a1a1a]">{point.value}</span>
                    {point.trend === "up" ? <TrendingUp size={14} className="text-[#7fb069]" /> : null}
                  </div>
                </div>
              ))}
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
                      selected ? "text-[#1a1a1a]" : "text-[#999]"
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
                <div className="rounded-lg border border-black/10 bg-white p-4">
                  <div className="flex items-center justify-between text-xs font-semibold text-[#666]">
                    <span>Prep window</span>
                    <span className="flex items-center gap-2 text-[#1a1a1a]">
                      <Clock size={14} />
                      7:26 remaining
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-[#1a1a1a]">
                    Outline your anchors, concessions, and questions before the call begins.
                  </p>
                </div>
                <textarea
                  value={notes}
                  onChange={(event) => onNotesChange(event.target.value)}
                  placeholder="Write your notes, anchors, and fallback offers..."
                  className="h-72 w-full resize-none rounded-lg border border-black/10 bg-white p-4 text-sm text-[#1a1a1a] outline-none focus:border-[#7fb069]"
                />
                <div className="rounded-lg border border-black/10 bg-[#f5faf3] p-4 text-sm text-[#666]">
                  Tip: Keep your opening number 10-15% above your target. Let the opponent come up to you.
                </div>
              </Tab.Panel>
              <Tab.Panel className="space-y-4">
                {coachSuggestions.map((suggestion) => (
                  <Disclosure key={suggestion.id}>
                    {({ open }) => (
                      <div className="rounded-xl border border-black/10 bg-white p-4">
                        <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-[0.2em] text-[#7fb069]">
                          <span>{suggestion.category}</span>
                          <span className="text-[#999]">{suggestion.time}</span>
                        </div>
                        <p className={`mt-3 text-sm text-[#1a1a1a] ${open ? "" : "coach-blur"}`}>
                          {suggestion.text}
                        </p>
                        <div className="mt-4 flex items-center justify-between">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              suggestion.priority === "high"
                                ? "bg-[#1a1a1a] text-white"
                                : "bg-black/5 text-[#666]"
                            }`}
                          >
                            {suggestion.priority} priority
                          </span>
                          <Disclosure.Button className="text-xs font-semibold text-[#1a1a1a] cursor-pointer">
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
