"use client";

import { Button, Switch } from "@headlessui/react";
import { Mic, MicOff, PhoneOff, Video, VideoOff } from "lucide-react";

type CallControlsProps = {
  isMuted: boolean;
  onMutedChange: (value: boolean) => void;
  isVideoOff: boolean;
  onVideoChange: (value: boolean) => void;
  onEndSession: () => void;
};

export function CallControls({
  isMuted,
  onMutedChange,
  isVideoOff,
  onVideoChange,
  onEndSession,
}: CallControlsProps) {
  return (
    <div className="absolute bottom-0 left-0 right-0 flex justify-center bg-gradient-to-t from-black/80 via-black/40 to-transparent px-6 py-8">
      <div className="flex items-center gap-3">
        <Switch
          checked={!isMuted}
          onChange={() => onMutedChange(!isMuted)}
          className={`flex h-14 w-14 items-center justify-center rounded-full border transition cursor-pointer ${
            isMuted ? "bg-danger border-transparent" : "bg-white/15 border-white/20 hover:bg-white/25"
          }`}
        >
          <span className="sr-only">Toggle microphone</span>
          {isMuted ? <MicOff size={22} /> : <Mic size={22} />}
        </Switch>
        <Switch
          checked={!isVideoOff}
          onChange={() => onVideoChange(!isVideoOff)}
          className={`flex h-14 w-14 items-center justify-center rounded-full border transition cursor-pointer ${
            isVideoOff
              ? "bg-danger border-transparent"
              : "bg-white/15 border-white/20 hover:bg-white/25"
          }`}
        >
          <span className="sr-only">Toggle camera</span>
          {isVideoOff ? <VideoOff size={22} /> : <Video size={22} />}
        </Switch>
        <Button
          type="button"
          onClick={onEndSession}
          className="flex h-14 w-14 items-center justify-center rounded-full bg-danger text-white shadow-danger-glow transition hover-bg-danger-dark cursor-pointer"
        >
          <PhoneOff size={22} />
        </Button>
      </div>
    </div>
  );
}
