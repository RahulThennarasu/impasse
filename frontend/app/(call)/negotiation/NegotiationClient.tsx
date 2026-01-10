"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@headlessui/react";
import { Maximize2 } from "lucide-react";
import { CallControls } from "./CallControls";
import { CallHeader } from "./CallHeader";
import { OpponentOrb } from "./OpponentOrb";
import { WorkspaceSidebar } from "./WorkspaceSidebar";
import {
  getWsBaseUrl,
  requestPostMortem,
  type CoachTip,
  type ScenarioContext,
} from "@/lib/api";

const initialCoachSuggestions: CoachTip[] = [
  {
    id: "tip-1",
    text: "Good rapport building. They're receptive to your approach.",
    time: "Just now",
    priority: "high",
    category: "Rapport",
  },
  {
    id: "tip-2",
    text: "Consider slowing your pace. Pauses show confidence.",
    time: "2 min ago",
    priority: "medium",
    category: "Delivery",
  },
];

const keyPoints = [
  { label: "Rapport Score", value: "8.5/10", trend: "up" as const },
  { label: "Speaking Pace", value: "142 wpm", trend: "neutral" as const },
  { label: "Confidence", value: "High", trend: "up" as const },
];

const blobToBase64 = (blob: Blob) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result;
      if (typeof result === "string") {
        const [, base64] = result.split(",");
        resolve(base64 ?? "");
      } else {
        reject(new Error("Failed to read blob"));
      }
    };
    reader.onerror = () => reject(new Error("Failed to read blob"));
    reader.readAsDataURL(blob);
  });

export function NegotiationClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("sessionId") ?? "";
  const agentId = searchParams.get("agentId") ?? "opponent";

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const videoTimerRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);

  const [notes, setNotes] = useState("");
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sessionTime] = useState(754);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [testAudioOn, setTestAudioOn] = useState(false);
  const [debugThinking, setDebugThinking] = useState(false);
  const [spinTrigger, setSpinTrigger] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [agentActivity, setAgentActivity] = useState(0);
  const [agentStatus, setAgentStatus] = useState<"idle" | "thinking" | "speaking" | "disconnected">(
    "disconnected"
  );
  const [coachSuggestions, setCoachSuggestions] = useState<CoachTip[]>(initialCoachSuggestions);
  const [scenario, setScenario] = useState<ScenarioContext | null>(null);

  const activeLevel = testAudioOn ? audioLevel : agentActivity;
  const isThinking = agentStatus === "thinking" || debugThinking;
  const statusLabel =
    agentStatus === "disconnected"
      ? "Disconnected"
      : agentStatus === "thinking"
        ? "Thinking"
        : agentStatus === "speaking"
          ? "Speaking"
          : "Idle";

  useEffect(() => {
    if (!sessionId) return;
    const stored = sessionStorage.getItem(`scenario:${sessionId}`);
    if (stored) {
      try {
        setScenario(JSON.parse(stored));
      } catch {
        setScenario(null);
      }
    }
  }, [sessionId]);

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
      } catch (error) {
        setMediaError("Unable to access camera or microphone.");
      }
    };

    startCapture();

    return () => {
      active = false;
      setStream((current) => {
        current?.getTracks().forEach((track) => track.stop());
        return null;
      });
    };
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
      } catch {
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
    await context.resume();
    try {
      await audioRef.current.play();
    } catch {
      setMediaError("Unable to play test audio. Check your browser permissions.");
    }
  }, []);

  const stopTestAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    analyserRef.current = null;
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

  useEffect(() => {
    if (!sessionId) return;
    const wsUrl = `${getWsBaseUrl()}/api/v1/ws/video/call/${sessionId}/${agentId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setAgentStatus("idle");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "call_status" && data.status === "connected") {
          setAgentStatus("idle");
        }
        if (data.type === "call_status") {
          if (data.status === "connected") {
            setAgentStatus("idle");
          }
          if (data.status === "ended") {
            setAgentStatus("disconnected");
          }
        }
        if (data.type === "agent_response") {
          setAgentStatus("thinking");
        }
        if (data.type === "message_received") {
          setCoachSuggestions((prev) => [
            {
              id: `coach-${Date.now()}`,
              text: `You: ${data.message ?? "Message sent"}`,
              time: "now",
              priority: "low",
              category: "Transcript",
            },
            ...prev,
          ]);
        }
        if (data.type === "transcript" && Array.isArray(data.transcript)) {
          const latest = data.transcript.at(-1);
          if (latest?.message) {
            setCoachSuggestions((prev) => [
              {
                id: `coach-${Date.now()}`,
                text: `${latest.role ?? "user"}: ${latest.message}`,
                time: "now",
                priority: "low",
                category: "Transcript",
              },
              ...prev,
            ]);
          }
        }
        if (data.type === "agent_audio" && data.audio_base64) {
          const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
          setAgentStatus("speaking");
          setAgentActivity(0.9);
          audio.onended = () => {
            setAgentStatus("idle");
            setAgentActivity(0);
          };
          audio.play().catch(() => {
            setAgentStatus("idle");
            setAgentActivity(0);
          });
        }
      } catch {
        setMediaError("Received malformed socket message.");
      }
    };

    ws.onclose = () => {
      setAgentStatus("disconnected");
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [sessionId, agentId]);

  useEffect(() => {
    if (!stream || !wsRef.current) return;
    const ws = wsRef.current;
    const sendIfOpen = (payload: Record<string, unknown>) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
      }
    };

    const audioTracks = stream.getAudioTracks();
    if (audioTracks.length) {
      const audioStream = new MediaStream(audioTracks);
      const recorder = new MediaRecorder(audioStream, {
        mimeType: "audio/webm;codecs=opus",
      });
      recorderRef.current = recorder;
      recorder.ondataavailable = async (event) => {
        if (event.data.size === 0) return;
        try {
          const base64 = await blobToBase64(event.data);
          sendIfOpen({ type: "audio_data", data: base64 });
        } catch {
          setMediaError("Failed to encode audio stream.");
        }
      };
      recorder.start(500);
    }

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const sendFrame = () => {
      if (!videoRef.current || !ctx) return;
      const video = videoRef.current;
      if (video.videoWidth === 0) return;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.6);
      sendIfOpen({ type: "video_frame", data: dataUrl });
    };
    videoTimerRef.current = window.setInterval(sendFrame, 350);

    return () => {
      recorderRef.current?.stop();
      recorderRef.current = null;
      if (videoTimerRef.current) {
        window.clearInterval(videoTimerRef.current);
      }
    };
  }, [stream]);

  const handleEndSession = async () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: "end_call" }));
    }
    if (sessionId) {
      try {
        await requestPostMortem(sessionId);
      } catch {
        setMediaError("Failed to request post-mortem analysis.");
      }
    }
    router.push(`/postmortem/${sessionId || "current-session"}`);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const headerTitle = scenario?.title ?? "Negotiation Session";
  const headerSubtitle = scenario
    ? `Role: ${scenario.role} • ${scenario.description}`
    : "Opponent: AI Agent • Scenario loading";

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
          title={headerTitle}
          subtitle={headerSubtitle}
          testAudioOn={testAudioOn}
          onTestAudioChange={setTestAudioOn}
          isThinking={isThinking}
          onThinkingChange={(next) => {
            setDebugThinking(next);
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
            audioLevel={activeLevel}
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
    </div>
  );
}