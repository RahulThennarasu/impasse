"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Dialog, DialogPanel, DialogTitle } from "@headlessui/react";
import { Maximize2 } from "lucide-react";
import { CallControls } from "./CallControls";
import { CallHeader } from "./CallHeader";
import { OpponentOrb } from "./OpponentOrb";
import { useNegotiation } from "./NegotiationContext";
import { WorkspaceSidebar } from "./WorkspaceSidebar";
import {
  getWsBaseUrl,
  requestPostMortem,
  type CoachTip,
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

const base64ToArrayBuffer = (base64: string) => {
  const binary = atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
};

const pcm16ToFloat32 = (buffer: ArrayBuffer): Float32Array => {
  const int16 = new Int16Array(buffer);
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i += 1) {
    float32[i] = int16[i] / 32768;
  }
  return float32;
};

const downsampleBuffer = (
  input: Float32Array,
  inputSampleRate: number,
  outputSampleRate: number
) => {
  if (outputSampleRate === inputSampleRate) {
    return input;
  }
  const ratio = inputSampleRate / outputSampleRate;
  const newLength = Math.round(input.length / ratio);
  const result = new Float32Array(newLength);
  let offsetResult = 0;
  let offsetBuffer = 0;
  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
    let accum = 0;
    let count = 0;
    for (
      let i = offsetBuffer;
      i < nextOffsetBuffer && i < input.length;
      i += 1
    ) {
      accum += input[i];
      count += 1;
    }
    result[offsetResult] = accum / Math.max(count, 1);
    offsetResult += 1;
    offsetBuffer = nextOffsetBuffer;
  }
  return result;
};

const floatTo16BitPCM = (input: Float32Array) => {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i += 1) {
    const s = Math.max(-1, Math.min(1, input[i]));
    output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return output;
};

export function NegotiationClient() {
  const router = useRouter();
  const {
    sessionId,
    scenario,
    notes,
    phase,
    notesRemaining,
    callRemaining,
    setNotes,
    startCall,
    markCallStarted,
    endCall,
    callStartedAt,
    setNotesRemaining,
  } = useNegotiation();

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const ttsContextRef = useRef<AudioContext | null>(null);
  const ttsQueueEndRef = useRef<number>(0);
  const ttsEndTimerRef = useRef<number | null>(null);
  const inputContextRef = useRef<AudioContext | null>(null);
  const inputProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const inputGainRef = useRef<GainNode | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const rafRef = useRef<number | null>(null);
  const autoEndRef = useRef(false);

  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [testAudioOn, setTestAudioOn] = useState(false);
  const [debugThinking, setDebugThinking] = useState(false);
  const [spinTrigger, setSpinTrigger] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [agentActivity, setAgentActivity] = useState(0);
  const [socketReady, setSocketReady] = useState(false);
  const [agentStatus, setAgentStatus] = useState<
    "idle" | "thinking" | "speaking" | "disconnected"
  >("disconnected");
  const [coachSuggestions, setCoachSuggestions] = useState<CoachTip[]>(
    initialCoachSuggestions
  );

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
    let active = true;

    const startCapture = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: true,
        });
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

    if (phase === "call") {
      startCapture();
    }

    return () => {
      active = false;
      setStream((current) => {
        current?.getTracks().forEach((track) => track.stop());
        return null;
      });
    };
  }, [phase]);

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
      const audio = new Audio("/test.m4a");
      audio.loop = true;
      audio.preload = "auto";
      audioRef.current = audio;
    }
    if (audioContextRef.current) {
      await audioContextRef.current.resume();
      try {
        await audioRef.current?.play();
      } catch {
        setMediaError(
          "Unable to play test audio. Check your browser permissions."
        );
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
      setMediaError(
        "Unable to play test audio. Check your browser permissions."
      );
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
    if (phase !== "call" && testAudioOn) {
      setTestAudioOn(false);
    }
  }, [phase, testAudioOn]);

  useEffect(() => {
    return () => {
      stopTestAudio();
      if (ttsEndTimerRef.current) {
        window.clearTimeout(ttsEndTimerRef.current);
      }
      if (ttsContextRef.current) {
        ttsContextRef.current.close();
        ttsContextRef.current = null;
      }
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
    if (!sessionId || phase !== "call") return;
    const wsUrl = `${getWsBaseUrl()}/api/v1/ws/negotiation/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    setSocketReady(false);

    ws.onopen = () => {
      const scenarioPayload =
        scenario &&
        "opponent" in (scenario as Record<string, unknown>) &&
        "coach" in (scenario as Record<string, unknown>)
          ? scenario
          : {
              opponent: {
                title: scenario?.title ?? "Negotiation Practice",
                role: scenario?.role ?? "Opponent",
                description:
                  scenario?.description ?? "Practice negotiation scenario",
              },
              coach: {
                title: "Coach",
                role: "Coach",
                description: "Provide negotiation tips and guidance.",
              },
            };
      ws.send(
        JSON.stringify({ type: "initialize", scenario: scenarioPayload })
      );
      setSocketReady(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "ready") {
          setAgentStatus("idle");
        }
        if (data.type === "error") {
          setMediaError(data.message ?? "Server error");
        }
        if (data.type === "transcription") {
          setCoachSuggestions((prev) => [
            {
              id: `coach-${Date.now()}`,
              text: data.text ?? "Transcribing...",
              time: "now",
              priority: "low",
              category: "Transcript",
            },
            ...prev,
          ]);
        }
        if (data.type === "opponent_opening" || data.type === "opponent_text") {
          setAgentStatus("thinking");
          setCoachSuggestions((prev) => [
            {
              id: `coach-${Date.now()}`,
              text: data.text ?? "Opponent response",
              time: "now",
              priority: "medium",
              category: "Opponent",
            },
            ...prev,
          ]);
        }
        if (data.type === "coach_tip") {
          setCoachSuggestions((prev) => [
            {
              id: `coach-${Date.now()}`,
              text: data.text ?? "Coach tip",
              time: "now",
              priority: "high",
              category: "Coach",
            },
            ...prev,
          ]);
        }
        if (data.type === "audio_start") {
          setAgentStatus("speaking");
          setAgentActivity(0.85);
          if (ttsContextRef.current) {
            ttsQueueEndRef.current = ttsContextRef.current.currentTime;
            void ttsContextRef.current.resume();
          }
        }
        if (data.type === "audio_chunk" && data.data) {
          const buffer = base64ToArrayBuffer(data.data);
          const pcm = pcm16ToFloat32(buffer);
          let energy = 0;
          let count = 0;
          for (let i = 0; i < pcm.length; i += 8) {
            const sample = pcm[i] ?? 0;
            energy += sample * sample;
            count += 1;
          }
          const rms = Math.sqrt(energy / Math.max(count, 1));
          setAgentActivity(Math.min(1, rms * 1.6));
          const context =
            ttsContextRef.current ?? new AudioContext({ sampleRate: 44100 });
          ttsContextRef.current = context;
          void context.resume();
          const audioBuffer = context.createBuffer(1, pcm.length, 44100);
          audioBuffer.copyToChannel(pcm, 0);
          const source = context.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(context.destination);
          const startTime = Math.max(
            context.currentTime,
            ttsQueueEndRef.current
          );
          source.start(startTime);
          ttsQueueEndRef.current = startTime + audioBuffer.duration;
        }
        if (data.type === "audio_end") {
          if (ttsEndTimerRef.current) {
            window.clearTimeout(ttsEndTimerRef.current);
          }
          const context = ttsContextRef.current;
          const remaining = context
            ? Math.max(0, ttsQueueEndRef.current - context.currentTime)
            : 0;
          ttsEndTimerRef.current = window.setTimeout(() => {
            setAgentStatus("idle");
            setAgentActivity(0);
          }, remaining * 1000 + 40);
        }
        if (data.type === "negotiation_complete") {
          setAgentStatus("idle");
        }
      } catch {
        setMediaError("Received malformed socket message.");
      }
    };

    ws.onclose = () => {
      setAgentStatus("disconnected");
      setSocketReady(false);
    };

    ws.onerror = () => {
      setMediaError("WebSocket connection failed.");
      setSocketReady(false);
    };

    return () => {
      ws.close();
      wsRef.current = null;
      setSocketReady(false);
    };
  }, [sessionId, scenario, phase]);

  useEffect(() => {
    if (!stream || !wsRef.current || !socketReady || phase !== "call") return;
    const ws = wsRef.current;
    if (ws.readyState !== WebSocket.OPEN) return;
    const context = new AudioContext({ sampleRate: 16000 });
    inputContextRef.current = context;
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);
    const gain = context.createGain();
    gain.gain.value = 0;
    inputGainRef.current = gain;
    inputProcessorRef.current = processor;

    processor.onaudioprocess = (event) => {
      if (ws.readyState !== WebSocket.OPEN || isMuted) return;
      const input = event.inputBuffer.getChannelData(0);
      const resampled = downsampleBuffer(input, context.sampleRate, 16000);
      const pcm16 = floatTo16BitPCM(resampled);
      ws.send(pcm16.buffer);
    };

    source.connect(processor);
    processor.connect(gain);
    gain.connect(context.destination);

    return () => {
      processor.disconnect();
      source.disconnect();
      gain.disconnect();
      inputProcessorRef.current = null;
      inputGainRef.current = null;
      context.close();
      inputContextRef.current = null;
    };
  }, [stream, isMuted, socketReady, phase]);

  const handleEndSession = async () => {
    autoEndRef.current = true;
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: "end_negotiation" }));
    }
    endCall();
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

  useEffect(() => {
    if (phase === "call" && socketReady && !callStartedAt) {
      markCallStarted();
    }
  }, [phase, socketReady, callStartedAt, markCallStarted]);

  useEffect(() => {
    if (phase === "ended" && !autoEndRef.current) {
      autoEndRef.current = true;
      handleEndSession();
    }
  }, [phase]);

  if (phase !== "call") {
    return (
      <div className="relative min-h-screen bg-night text-white">
        <div className="mx-auto flex max-w-5xl flex-col gap-6 px-8 pb-20 pt-12">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.28em] text-olive-soft">
                Note-taking phase
              </div>
              <h1 className="mt-3 text-3xl font-serif text-white">
                {headerTitle}
              </h1>
              <p className="mt-2 max-w-2xl text-sm text-white/70">
                {headerSubtitle}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-full border border-white/10 bg-black/60 px-5 py-3 text-sm font-semibold text-white">
                {formatTime(notesRemaining)}
              </div>
              <Button
                type="button"
                onClick={() => setNotesRemaining(5)}
                className="rounded-full border border-white/10 bg-black/50 px-4 py-2 text-xs font-semibold text-white/80 transition hover:bg-black/70 cursor-pointer"
              >
                Debug: set 5s left
              </Button>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
              <h2 className="text-lg font-semibold text-white">Your notes</h2>
              <p className="mt-2 text-sm text-white/60">
                Capture anchors, concessions, and must-haves before the call starts.
              </p>
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Outline your goals, walkaway points, and key questions..."
                className="mt-4 h-72 w-full resize-none rounded-xl border border-white/10 bg-black/50 p-4 text-sm text-white outline-none focus-border-olive"
              />
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/40 p-6">
              <h2 className="text-lg font-semibold text-white">Scenario brief</h2>
              <p className="mt-2 text-sm text-white/60">
                {scenario?.description ?? "Scenario details will appear once generated."}
              </p>
              <div className="mt-6 rounded-xl border border-white/10 bg-black/60 p-4 text-sm text-white/70">
                <div className="text-xs font-semibold uppercase tracking-[0.2em] text-olive-soft">
                  Your role
                </div>
                <div className="mt-2 text-base text-white">
                  {scenario?.role ?? "Negotiator"}
                </div>
              </div>
              <div className="mt-4 rounded-xl border border-white/10 bg-black/60 p-4 text-sm text-white/70">
                <div className="text-xs font-semibold uppercase tracking-[0.2em] text-olive-soft">
                  Timer
                </div>
                <div className="mt-2 text-base text-white">
                  {formatTime(notesRemaining)} remaining
                </div>
              </div>
            </div>
          </div>
        </div>

        <Dialog open={phase === "ready"} onClose={() => null} className="relative z-50">
          <div className="fixed inset-0 bg-black/70" aria-hidden="true" />
          <div className="fixed inset-0 flex items-center justify-center p-6">
            <DialogPanel className="w-full max-w-md rounded-2xl border border-white/10 bg-black/90 p-8 text-white shadow-2xl">
              <DialogTitle className="text-xl font-semibold text-white">
                Notes time complete
              </DialogTitle>
              <p className="mt-3 text-sm text-white/70">
                Your 15 minutes are up. Start the negotiation when you're ready.
              </p>
              <Button
                type="button"
                onClick={startCall}
                className="mt-6 w-full rounded-full bg-olive px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg cursor-pointer"
              >
                Start negotiation
              </Button>
            </DialogPanel>
          </div>
        </Dialog>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-night text-white">
      <WorkspaceSidebar
        isSidebarOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        coachSuggestions={coachSuggestions}
        notes={notes}
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
          timeLabel={formatTime(callRemaining)}
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
            className="h-full w-full object-cover scale-x-[-1]"
          />
          {isVideoOff || !stream ? (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-sm font-semibold text-white/80">
              {isVideoOff ? "Camera paused" : "Connecting camera..."}
            </div>
          ) : null}
          <div className="absolute right-8 top-6 flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-4 py-2 text-xs font-semibold text-white backdrop-blur">
            <span className="h-2 w-2 rounded-full bg-olive-soft shadow-olive-glow" />
            LIVE
          </div>
          <div className="absolute right-8 top-16 rounded-full border border-white/10 bg-black/40 px-3 py-2 text-[10px] font-semibold text-white/70 backdrop-blur">
            <Button
              type="button"
              onClick={handleEndSession}
              className="cursor-pointer"
            >
              Debug: end session
            </Button>
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
