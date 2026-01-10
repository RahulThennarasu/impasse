"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@headlessui/react";
import { Maximize2 } from "lucide-react";
import { CallControls } from "./CallControls";
import { CallHeader } from "./CallHeader";
import { OpponentOrb } from "./OpponentOrb";
import { WorkspaceSidebar } from "./WorkspaceSidebar";
import { UploadModal } from "@/components/UploadModal";
import { uploadNegotiationVideo } from "@/lib/api";

const coachSuggestions = [
  {
    id: 1,
    text: "Good rapport building. They're receptive to your approach.",
    time: "Just now",
    priority: "high",
    category: "Rapport",
  },
  {
    id: 2,
    text: "Consider slowing your pace. Pauses show confidence.",
    time: "2 min ago",
    priority: "medium",
    category: "Delivery",
  },
  {
    id: 3,
    text: "They're showing interest. This is a good moment to anchor high.",
    time: "5 min ago",
    priority: "high",
    category: "Strategy",
  },
  {
    id: 4,
    text: "Watch their body language. They seem hesitant about pricing.",
    time: "7 min ago",
    priority: "medium",
    category: "Observation",
  },
];

const keyPoints = [
  { label: "Rapport Score", value: "8.5/10", trend: "up" as const },
  { label: "Speaking Pace", value: "142 wpm", trend: "neutral" as const },
  { label: "Confidence", value: "High", trend: "up" as const },
];

export function NegotiationClient() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioNodesRef = useRef<{
    mediaSource?: MediaElementAudioSourceNode;
    gain?: GainNode;
  } | null>(null);
  const rafRef = useRef<number | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const [notes, setNotes] = useState("");
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sessionTime, setSessionTime] = useState(0);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [testAudioOn, setTestAudioOn] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [spinTrigger, setSpinTrigger] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const sessionIdRef = useRef<string>(crypto.randomUUID());

  const statusLabel = isThinking
    ? "Thinking"
    : testAudioOn && audioLevel > 0.06
      ? "Speaking"
      : testAudioOn
        ? "Listening"
        : "Idle";

  useEffect(() => {
    let active = true;

    const startCapture = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
        if (!active) {
          mediaStream.getTracks().forEach((track) => track.stop());
          return;
        }
        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }

        // Start recording
        const mediaRecorder = new MediaRecorder(mediaStream, {
          mimeType: "video/webm;codecs=vp9,opus",
        });
        mediaRecorderRef.current = mediaRecorder;
        recordedChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            recordedChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = () => {
          const blob = new Blob(recordedChunksRef.current, { type: "video/webm" });
          setRecordedBlob(blob);
        };

        mediaRecorder.start(1000); // Collect data every second
      } catch (error) {
        setMediaError("Unable to access camera or microphone.");
      }
    };

    startCapture();

    return () => {
      active = false;
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      setStream((current) => {
        current?.getTracks().forEach((track) => track.stop());
        return null;
      });
    };
  }, []);

  // Session timer
  useEffect(() => {
    const interval = setInterval(() => {
      setSessionTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!stream) return;
    stream.getAudioTracks().forEach((track) => {
      track.enabled = !isMuted;
    });
  }, [isMuted, stream]);

  useEffect(() => {
    if (!stream) return;
    stream.getVideoTracks().forEach((track) => {
      track.enabled = !isVideoOff;
    });
  }, [isVideoOff, stream]);

  const startTestAudio = useCallback(async () => {
    if (!audioRef.current) {
      const audio = new Audio("/test-loop.mp3");
      audio.loop = true;
      audio.preload = "auto";
      audioRef.current = audio;
    }
    if (audioContextRef.current) {
      await audioContextRef.current.resume();
      try {
        await audioRef.current?.play();
      } catch (error) {
        setMediaError("Unable to play test audio. Check your browser permissions.");
      }
      return;
    }
    const context = new AudioContext();
    const analyser = context.createAnalyser();
    analyser.fftSize = 256;
    const gain = context.createGain();
    gain.gain.value = 0.6;
    const mediaSource = context.createMediaElementSource(audioRef.current);
    mediaSource.connect(gain);
    gain.connect(analyser);
    analyser.connect(context.destination);
    audioContextRef.current = context;
    analyserRef.current = analyser;
    audioNodesRef.current = { mediaSource, gain };
    await context.resume();
    try {
      await audioRef.current.play();
    } catch (error) {
      setMediaError("Unable to play test audio. Check your browser permissions.");
    }
  }, []);

  const stopTestAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    audioNodesRef.current = null;
    analyserRef.current = null;
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (testAudioOn) {
      startTestAudio();
    } else {
      stopTestAudio();
      setAudioLevel(0);
    }
  }, [testAudioOn, startTestAudio, stopTestAudio]);

  useEffect(() => {
    return () => {
      stopTestAudio();
    };
  }, [stopTestAudio]);

  useEffect(() => {
    if (!testAudioOn || !analyserRef.current) return;
    const analyser = analyserRef.current;
    const data = new Uint8Array(analyser.frequencyBinCount);

    const tick = () => {
      analyser.getByteFrequencyData(data);
      const sum = data.reduce((acc, value) => acc + value, 0);
      setAudioLevel(sum / data.length / 255);
      rafRef.current = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [testAudioOn]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleEndSession = useCallback(() => {
    // Stop recording and trigger the onstop handler
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    // Show the upload modal
    setIsUploadModalOpen(true);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!recordedBlob) {
      throw new Error("No recording available");
    }
    await uploadNegotiationVideo(sessionIdRef.current, recordedBlob);
  }, [recordedBlob]);

  const handleNavigateToPostMortem = useCallback(() => {
    // Stop all tracks
    stream?.getTracks().forEach((track) => track.stop());
    router.push("/postmortem/current-session");
  }, [router, stream]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-night text-white">
      <WorkspaceSidebar
        isSidebarOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        keyPoints={keyPoints}
        coachSuggestions={coachSuggestions}
        notes={notes}
        onNotesChange={setNotes}
      />

      <main className="relative flex h-full flex-1 flex-col">
        {!isSidebarOpen && (
          <Button
            type="button"
            onClick={() => setIsSidebarOpen(true)}
            className="absolute left-4 top-6 z-30 flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-2 text-xs font-semibold text-white backdrop-blur cursor-pointer"
          >
            <Maximize2 size={14} />
            Workspace
          </Button>
        )}

        <CallHeader
          timeLabel={formatTime(sessionTime)}
          testAudioOn={testAudioOn}
          onTestAudioChange={setTestAudioOn}
          isThinking={isThinking}
          onThinkingChange={(next) => {
            setIsThinking(next);
            if (next) {
              setSpinTrigger((prev) => prev + 1);
            }
          }}
        />

        <div className="relative flex flex-1 items-center justify-center overflow-hidden">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="h-full w-full object-cover"
          />
          {isVideoOff || !stream ? (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-sm font-semibold text-white/80">
              {isVideoOff ? "Camera paused" : "Connecting camera..."}
            </div>
          ) : null}
          <div className="absolute left-8 top-6 flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-4 py-2 text-xs font-semibold text-white backdrop-blur">
            <span className="h-2 w-2 rounded-full bg-olive-soft shadow-olive-glow" />
            LIVE
          </div>
          <div className="absolute right-8 top-6 rounded-full border border-white/10 bg-black/40 px-4 py-2 text-xs font-semibold text-white backdrop-blur">
            {formatTime(sessionTime)}
          </div>

          <OpponentOrb
            isThinking={isThinking}
            spinTrigger={spinTrigger}
            statusLabel={statusLabel}
            audioLevel={audioLevel}
          />

          {mediaError ? (
            <div className="absolute bottom-28 left-1/2 -translate-x-1/2 rounded-full bg-danger-muted px-4 py-2 text-xs font-semibold text-white shadow-lg">
              {mediaError}
            </div>
          ) : null}
        </div>

        <CallControls
          isMuted={isMuted}
          onMutedChange={setIsMuted}
          isVideoOff={isVideoOff}
          onVideoChange={setIsVideoOff}
          onEndSession={handleEndSession}
        />
      </main>

      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={handleNavigateToPostMortem}
        onConfirmUpload={handleUpload}
        onSkip={handleNavigateToPostMortem}
        sessionDuration={formatTime(sessionTime)}
      />
    </div>
  );
}
