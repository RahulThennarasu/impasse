"use client";

import { Switch } from "@headlessui/react";
import { Clock } from "lucide-react";

type CallHeaderProps = {
  timeLabel: string;
  title: string;
  subtitle: string;
  testAudioOn: boolean;
  onTestAudioChange: (value: boolean) => void;
  isThinking: boolean;
  onThinkingChange: (value: boolean) => void;
};

export function CallHeader({
  timeLabel,
  title,
  subtitle,
  testAudioOn,
  onTestAudioChange,
  isThinking,
  onThinkingChange,
}: CallHeaderProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 px-6 py-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">Live negotiation</p>
        <h1 className="mt-2 text-2xl font-serif text-white">{title}</h1>
        <p className="text-sm text-white/60">{subtitle}</p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white">
          <Clock size={14} />
          {timeLabel} remaining
        </div>
        <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-white">
          <span className="uppercase tracking-[0.18em] text-white/70">Thinking</span>
          <Switch
            checked={isThinking}
            onChange={onThinkingChange}
            className={`relative flex h-6 w-11 items-center rounded-full border transition cursor-pointer ${
              isThinking ? "border-olive bg-olive" : "border-white/20 bg-white/10"
            }`}
          >
            <span className="sr-only">Toggle thinking state</span>
            <span
              className={`inline-block h-4 w-4 rounded-full bg-white transition ${
                isThinking ? "translate-x-5" : "translate-x-1"
              }`}
            />
          </Switch>
        </div>
        <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-white">
          <span className="uppercase tracking-[0.18em] text-white/70">Test audio</span>
          <Switch
            checked={testAudioOn}
            onChange={onTestAudioChange}
            className={`relative flex h-6 w-11 items-center rounded-full border transition cursor-pointer ${
              testAudioOn ? "border-olive bg-olive" : "border-white/20 bg-white/10"
            }`}
          >
            <span className="sr-only">Toggle test audio</span>
            <span
              className={`inline-block h-4 w-4 rounded-full bg-white transition ${
                testAudioOn ? "translate-x-5" : "translate-x-1"
              }`}
            />
          </Switch>
        </div>
      </div>
    </div>
  );
}
