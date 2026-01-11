"use client";

import { Dialog, DialogPanel, DialogTitle } from "@headlessui/react";
import { Globe, Lock } from "lucide-react";

type VisibilityDialogProps = {
  isOpen: boolean;
  onSelect: (isPublic: boolean) => void;
};

export function VisibilityDialog({ isOpen, onSelect }: VisibilityDialogProps) {
  return (
    <Dialog open={isOpen} onClose={() => null} className="relative z-50">
      <div className="fixed inset-0 bg-black/80" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-6">
        <DialogPanel className="w-full max-w-md rounded-2xl border border-white/10 bg-night p-8 text-white shadow-2xl">
          <DialogTitle className="text-xl font-semibold text-white">
            Save your negotiation
          </DialogTitle>
          <p className="mt-3 text-sm text-white/70">
            Choose how you want to save this session. You can change this later.
          </p>

          <div className="mt-6 flex flex-col gap-3">
            <button
              type="button"
              onClick={() => onSelect(true)}
              className="flex items-center gap-4 rounded-xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-olive/50 hover:bg-olive/10 cursor-pointer"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-olive/20">
                <Globe className="h-6 w-6 text-olive-soft" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-white">Public</div>
                <div className="mt-1 text-sm text-white/60">
                  Share with the community. Others can learn from your session.
                </div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => onSelect(false)}
              className="flex items-center gap-4 rounded-xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-olive/50 hover:bg-olive/10 cursor-pointer"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/10">
                <Lock className="h-6 w-6 text-white/70" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-white">Private</div>
                <div className="mt-1 text-sm text-white/60">
                  Only you can view this session and analysis.
                </div>
              </div>
            </button>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  );
}
