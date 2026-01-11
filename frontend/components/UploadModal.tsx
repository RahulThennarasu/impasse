"use client";

import { useState } from "react";
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from "@headlessui/react";
import { Upload, X, Check, Loader2, Share2, Lock, Globe } from "lucide-react";

type UploadModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onConfirmUpload: (isPublic: boolean) => Promise<void>;
  onSkip: () => void;
  sessionDuration?: string;
};

type UploadState = "prompt" | "uploading" | "success" | "error";

export function UploadModal({
  isOpen,
  onClose,
  onConfirmUpload,
  onSkip,
  sessionDuration,
}: UploadModalProps) {
  const [uploadState, setUploadState] = useState<UploadState>("prompt");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPublic, setIsPublic] = useState(false);

  const handleUpload = async () => {
    setUploadState("uploading");
    setUploadProgress(0);

    try {
      await onConfirmUpload(isPublic);
      setUploadState("success");
    } catch (error) {
      setUploadState("error");
      setErrorMessage(error instanceof Error ? error.message : "Upload failed");
    }
  };

  const handleClose = () => {
    if (uploadState === "uploading") return;
    setUploadState("prompt");
    setUploadProgress(0);
    setErrorMessage(null);
    setIsPublic(false);
    onClose();
  };

  const handleSkip = () => {
    setUploadState("prompt");
    setIsPublic(false);
    onSkip();
  };

  return (
    <Dialog open={isOpen} onClose={handleClose} className="relative z-50">
      <DialogBackdrop className="fixed inset-0 bg-black/60 backdrop-blur-sm" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
          {uploadState === "prompt" && (
            <>
              <div className="mb-4 flex items-center justify-between">
                <DialogTitle className="text-xl font-bold text-ink">
                  Save Your Negotiation?
                </DialogTitle>
                <button
                  onClick={handleClose}
                  className="rounded-full p-1 text-muted hover:bg-black/5 hover:text-ink"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="mb-6">
                <div className="mb-4 flex items-center gap-3 rounded-xl bg-olive/10 p-4">
                  <Share2 className="text-olive" size={24} />
                  <div>
                    <p className="font-semibold text-ink">Save your recording</p>
                    <p className="text-sm text-muted">
                      Upload your negotiation to review later or share with others
                    </p>
                  </div>
                </div>

                {sessionDuration && (
                  <p className="mb-4 text-sm text-muted">
                    Session duration: <span className="font-medium text-ink">{sessionDuration}</span>
                  </p>
                )}

                {/* Public/Private Toggle */}
                <div className="rounded-xl border border-black/10 p-4">
                  <p className="mb-3 text-sm font-semibold text-ink">Visibility</p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setIsPublic(false)}
                      className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition ${
                        !isPublic
                          ? "bg-ink text-white"
                          : "bg-black/5 text-muted hover:bg-black/10"
                      }`}
                    >
                      <Lock size={16} />
                      Private
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsPublic(true)}
                      className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition ${
                        isPublic
                          ? "bg-olive text-white"
                          : "bg-black/5 text-muted hover:bg-black/10"
                      }`}
                    >
                      <Globe size={16} />
                      Public
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-muted">
                    {isPublic
                      ? "Anyone can view this recording to learn from your negotiation"
                      : "Only you can access this recording"}
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleSkip}
                  className="flex-1 rounded-full border-2 border-black/10 px-4 py-3 text-sm font-semibold text-muted transition hover:border-black/20 hover:bg-black/5"
                >
                  Skip
                </button>
                <button
                  onClick={handleUpload}
                  className="flex flex-1 items-center justify-center gap-2 rounded-full bg-ink px-4 py-3 text-sm font-bold text-white transition hover:bg-ink/90"
                >
                  <Upload size={16} />
                  Save Recording
                </button>
              </div>
            </>
          )}

          {uploadState === "uploading" && (
            <div className="py-8 text-center">
              <Loader2 size={48} className="mx-auto mb-4 animate-spin text-olive" />
              <DialogTitle className="mb-2 text-xl font-bold text-ink">
                Uploading...
              </DialogTitle>
              <p className="mb-4 text-sm text-muted">
                Please wait while we upload your recording
              </p>
              <div className="mx-auto h-2 w-full max-w-xs overflow-hidden rounded-full bg-black/10">
                <div
                  className="h-full bg-olive transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted">{Math.round(uploadProgress)}%</p>
            </div>
          )}

          {uploadState === "success" && (
            <div className="py-8 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-olive/20">
                <Check size={32} className="text-olive" />
              </div>
              <DialogTitle className="mb-2 text-xl font-bold text-ink">
                Upload Complete!
              </DialogTitle>
              <p className="mb-6 text-sm text-muted">
                {isPublic
                  ? "Your negotiation has been shared with the community"
                  : "Your negotiation has been saved privately"}
              </p>
              <button
                onClick={handleClose}
                className="rounded-full bg-ink px-6 py-3 text-sm font-bold text-white transition hover:bg-ink/90"
              >
                View Post-Mortem
              </button>
            </div>
          )}

          {uploadState === "error" && (
            <div className="py-8 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                <X size={32} className="text-red-500" />
              </div>
              <DialogTitle className="mb-2 text-xl font-bold text-ink">
                Upload Failed
              </DialogTitle>
              <p className="mb-6 text-sm text-muted">
                {errorMessage || "Something went wrong. Please try again."}
              </p>
              <div className="flex justify-center gap-3">
                <button
                  onClick={handleSkip}
                  className="rounded-full border-2 border-black/10 px-4 py-3 text-sm font-semibold text-muted transition hover:border-black/20 hover:bg-black/5"
                >
                  Skip
                </button>
                <button
                  onClick={handleUpload}
                  className="rounded-full bg-ink px-4 py-3 text-sm font-bold text-white transition hover:bg-ink/90"
                >
                  Try Again
                </button>
              </div>
            </div>
          )}
        </DialogPanel>
      </div>
    </Dialog>
  );
}
