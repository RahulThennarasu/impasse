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
  PostMortemError,
  startMultipartUpload,
  getPartUploadUrl,
  uploadPart,
  completeMultipartUpload,
  updatePostMortemVideoUrl,
  type CoachTip,
  type CompletedPart,
} from "@/lib/api";
import { VisibilityDialog } from "./VisibilityDialog";

const initialCoachSuggestions: CoachTip[] = [];

// S3 requires minimum 5MB per part (except last part)
const MIN_PART_SIZE = 5 * 1024 * 1024;

const base64ToArrayBuffer = (base64: string) => {
  const binary = atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
};

const pcm16ToFloat32 = (buffer: ArrayBuffer): Float32Array<ArrayBuffer> => {
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
  const ttsStartTimeRef = useRef<number>(0);
  const inputContextRef = useRef<AudioContext | null>(null);
  const inputProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const speechFrameCountRef = useRef(0);
  const lastBargeInRef = useRef(0);
  const inputGainRef = useRef<GainNode | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const rafRef = useRef<number | null>(null);
  const autoEndRef = useRef(false);
  const negotiationCompleteRef = useRef(false);
  const sessionDataStoredRef = useRef(false);
  const sessionDataStoredResolveRef = useRef<((value: boolean) => void) | null>(null);
  const ttsSourcesRef = useRef<AudioBufferSourceNode[]>([]);
  const isTtsPlayingRef = useRef(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);

  // Canvas recording refs for compositing user video + opponent orb
  const recordingCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const recordingCtxRef = useRef<CanvasRenderingContext2D | null>(null);
  const canvasAnimationRef = useRef<number | null>(null);
  const recordingAudioContextRef = useRef<AudioContext | null>(null);
  const recordingAudioDestRef = useRef<MediaStreamAudioDestinationNode | null>(null);
  const micSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  // Opponent orb state for canvas rendering
  const orbAudioLevelRef = useRef(0);
  const orbMotionPhaseRef = useRef(0);
  const orbIsThinkingRef = useRef(false);

  // Multipart upload refs for streaming
  const uploadIdRef = useRef<string | null>(null);
  const uploadedPartsRef = useRef<CompletedPart[]>([]);
  const partNumberRef = useRef(1);
  const pendingChunksRef = useRef<Blob[]>([]);
  const uploadingRef = useRef(false);

  const [isMuted, setIsMuted] = useState(false);
  const [isSkipConfirmOpen, setIsSkipConfirmOpen] = useState(false);
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
  const [showVisibilityDialog, setShowVisibilityDialog] = useState(false);
  const [isProcessingPostMortem, setIsProcessingPostMortem] = useState(false);
  const [processingStatus, setProcessingStatus] = useState("");

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

  // Sync orb state to refs for canvas recording
  useEffect(() => {
    orbAudioLevelRef.current = agentActivity;
  }, [agentActivity]);

  useEffect(() => {
    orbIsThinkingRef.current = isThinking;
  }, [isThinking]);

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

        // Start recording with streaming upload to S3
        // Use canvas compositing to capture both user video and opponent orb
        // Mix user mic audio with TTS audio for complete recording
        try {
          const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9,opus")
            ? "video/webm;codecs=vp9,opus"
            : "video/webm";

          // Create canvas for compositing video
          const canvas = document.createElement("canvas");
          canvas.width = 1280;
          canvas.height = 720;
          const ctx = canvas.getContext("2d");
          recordingCanvasRef.current = canvas;
          recordingCtxRef.current = ctx;

          // Create audio context for mixing mic + TTS
          const recordingAudioCtx = new AudioContext({ sampleRate: 44100 });
          const audioDest = recordingAudioCtx.createMediaStreamDestination();
          recordingAudioContextRef.current = recordingAudioCtx;
          recordingAudioDestRef.current = audioDest;

          // Connect user microphone to recording destination
          const micSource = recordingAudioCtx.createMediaStreamSource(mediaStream);
          micSource.connect(audioDest);
          micSourceRef.current = micSource;

          // Function to draw the opponent orb on canvas
          const drawOpponentOrb = (
            context: CanvasRenderingContext2D,
            audioLevel: number,
            motionPhase: number,
            isThinking: boolean
          ) => {
            const orbX = 40;
            const orbY = 40;
            const orbRadius = 56;

            // Draw orb background
            context.save();
            context.beginPath();
            context.arc(orbX + orbRadius, orbY + orbRadius, orbRadius, 0, Math.PI * 2);
            context.fillStyle = "rgba(0, 0, 0, 0.9)";
            context.fill();

            // Draw glow effect based on audio level
            const glowScale = 0.75 + audioLevel * 0.5;
            context.beginPath();
            context.arc(orbX + orbRadius, orbY + orbRadius, orbRadius * glowScale, 0, Math.PI * 2);
            context.fillStyle = `rgba(163, 190, 140, ${0.2 + audioLevel * 0.3})`;
            context.filter = "blur(16px)";
            context.fill();
            context.filter = "none";

            // Draw thinking ring if thinking
            if (isThinking) {
              context.beginPath();
              context.arc(orbX + orbRadius, orbY + orbRadius, orbRadius - 8, 0, Math.PI * 2);
              context.strokeStyle = `rgba(163, 190, 140, ${0.4 + Math.sin(motionPhase * 5) * 0.2})`;
              context.lineWidth = 1;
              context.stroke();
            }

            // Draw particles
            const seededRandom = (seed: number) => {
              let t = seed;
              return () => {
                t += 0x6d2b79f5;
                let m = Math.imul(t ^ (t >>> 15), 1 | t);
                m ^= m + Math.imul(m ^ (m >>> 7), 61 | m);
                return ((m ^ (m >>> 14)) >>> 0) / 4294967296;
              };
            };

            for (let i = 0; i < 48; i++) {
              const rng = seededRandom(i + 1);
              const angle = rng() * Math.PI * 2;
              const radius = Math.sqrt(rng()) * 32;
              const baseX = Math.cos(angle) * radius;
              const baseY = Math.sin(angle) * radius;
              const dx = rng() * 2 - 1;
              const dy = rng() * 2 - 1;
              const f1 = 0.6 + rng() * 0.9;
              const f2 = 0.7 + rng() * 1.1;
              const p1 = rng() * Math.PI * 2;
              const size = 3 + (i % 3) * 2;

              const phase = motionPhase + p1 * 0.4;
              const speedBoost = 1 + audioLevel * 1.8;
              const flowX = Math.cos(phase * f1) * 2.2 * speedBoost;
              const flowY = Math.sin(phase * f2) * 2.2 * speedBoost;
              const swirlX = Math.sin(phase + p1) * dx * 1.8 * speedBoost;
              const swirlY = Math.cos(phase + p1) * dy * 1.8 * speedBoost;
              const expansion = 0.7 + audioLevel * 0.55;
              const sizeBoost = 1 + audioLevel * 0.9;
              const x = (baseX + flowX + swirlX * 0.45) * expansion;
              const y = (baseY + flowY + swirlY * 0.45) * expansion;
              const opacity = 0.4 + audioLevel * 0.6;

              context.beginPath();
              context.arc(
                orbX + orbRadius + x,
                orbY + orbRadius + y,
                (size * sizeBoost) / 2,
                0,
                Math.PI * 2
              );
              context.fillStyle = `rgba(163, 190, 140, ${opacity})`;
              context.fill();
            }

            context.restore();

            // Draw status label
            context.save();
            context.fillStyle = "rgba(0, 0, 0, 0.4)";
            context.strokeStyle = "rgba(255, 255, 255, 0.2)";
            context.lineWidth = 1;
            const labelX = orbX;
            const labelY = orbY + orbRadius * 2 + 12;
            const labelWidth = 160;
            const labelHeight = 28;
            context.beginPath();
            context.roundRect(labelX, labelY, labelWidth, labelHeight, 14);
            context.fill();
            context.stroke();

            context.font = "12px system-ui, sans-serif";
            context.fillStyle = "white";
            context.textAlign = "left";
            context.textBaseline = "middle";
            const statusText = isThinking ? "Thinking" : audioLevel > 0.1 ? "Speaking" : "Idle";
            context.fillText(`Opponent status: ${statusText}`, labelX + 12, labelY + labelHeight / 2);
            context.restore();
          };

          // Animation loop to draw composited frame
          let lastFrameTime = 0;
          const targetFps = 30;
          const frameInterval = 1000 / targetFps;

          const drawFrame = (timestamp: number) => {
            if (!recordingCanvasRef.current || !recordingCtxRef.current || !videoRef.current) {
              canvasAnimationRef.current = requestAnimationFrame(drawFrame);
              return;
            }

            // Throttle to target FPS
            if (timestamp - lastFrameTime < frameInterval) {
              canvasAnimationRef.current = requestAnimationFrame(drawFrame);
              return;
            }
            lastFrameTime = timestamp;

            const context = recordingCtxRef.current;
            const video = videoRef.current;

            // Update motion phase
            orbMotionPhaseRef.current += 0.016 * (0.001 + orbAudioLevelRef.current * 0.002) * 60;

            // Clear and draw video (mirrored)
            context.save();
            context.translate(canvas.width, 0);
            context.scale(-1, 1);
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            context.restore();

            // Draw opponent orb overlay
            drawOpponentOrb(
              context,
              orbAudioLevelRef.current,
              orbMotionPhaseRef.current,
              orbIsThinkingRef.current
            );

            // Draw LIVE indicator
            context.save();
            context.fillStyle = "rgba(0, 0, 0, 0.4)";
            context.strokeStyle = "rgba(255, 255, 255, 0.1)";
            context.lineWidth = 1;
            context.beginPath();
            context.roundRect(canvas.width - 80, 24, 56, 28, 14);
            context.fill();
            context.stroke();

            // Green dot
            context.beginPath();
            context.arc(canvas.width - 64, 38, 4, 0, Math.PI * 2);
            context.fillStyle = "#a3be8c";
            context.shadowColor = "#a3be8c";
            context.shadowBlur = 8;
            context.fill();
            context.shadowBlur = 0;

            // LIVE text
            context.font = "bold 11px system-ui, sans-serif";
            context.fillStyle = "white";
            context.textAlign = "left";
            context.fillText("LIVE", canvas.width - 54, 42);
            context.restore();

            canvasAnimationRef.current = requestAnimationFrame(drawFrame);
          };

          canvasAnimationRef.current = requestAnimationFrame(drawFrame);

          // Get canvas stream and combine with mixed audio
          const canvasStream = canvas.captureStream(30);
          const combinedStream = new MediaStream([
            ...canvasStream.getVideoTracks(),
            ...audioDest.stream.getAudioTracks(),
          ]);

          const mediaRecorder = new MediaRecorder(combinedStream, { mimeType });
          mediaRecorderRef.current = mediaRecorder;
          recordedChunksRef.current = [];
          pendingChunksRef.current = [];
          uploadedPartsRef.current = [];
          partNumberRef.current = 1;
          uploadingRef.current = false;

          // Get sessionId from URL params
          const urlParams = new URLSearchParams(window.location.search);
          const currentSessionId = urlParams.get("sessionId");

          if (currentSessionId) {
            // Start multipart upload immediately
            startMultipartUpload(currentSessionId, mimeType)
              .then(({ upload_id }) => {
                uploadIdRef.current = upload_id;
                console.log(`Started multipart upload: ${upload_id}`);
              })
              .catch((err) => {
                console.error("Failed to start multipart upload:", err);
              });
          }

          // Helper function to upload accumulated chunks as a part
          const uploadAccumulatedChunks = async () => {
            if (uploadingRef.current || !uploadIdRef.current || !currentSessionId) {
              return;
            }

            const totalSize = pendingChunksRef.current.reduce((sum, chunk) => sum + chunk.size, 0);
            if (totalSize < MIN_PART_SIZE) {
              return; // Wait for more data
            }

            uploadingRef.current = true;
            const chunksToUpload = [...pendingChunksRef.current];
            pendingChunksRef.current = [];
            const partBlob = new Blob(chunksToUpload, { type: mimeType });
            const partNumber = partNumberRef.current;
            partNumberRef.current += 1;

            try {
              const { upload_url } = await getPartUploadUrl(
                currentSessionId,
                uploadIdRef.current,
                partNumber
              );
              const etag = await uploadPart(upload_url, partBlob);
              uploadedPartsRef.current.push({ part_number: partNumber, etag });
              console.log(`Uploaded part ${partNumber} (${(partBlob.size / 1024 / 1024).toFixed(2)}MB)`);
            } catch (err) {
              console.error(`Failed to upload part ${partNumber}:`, err);
              // Put chunks back for retry
              pendingChunksRef.current = [...chunksToUpload, ...pendingChunksRef.current];
              partNumberRef.current = partNumber;
            } finally {
              uploadingRef.current = false;
            }

            // Check if there are more chunks to upload
            const remainingSize = pendingChunksRef.current.reduce((sum, chunk) => sum + chunk.size, 0);
            if (remainingSize >= MIN_PART_SIZE) {
              void uploadAccumulatedChunks();
            }
          };

          mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              recordedChunksRef.current.push(event.data);
              pendingChunksRef.current.push(event.data);
              // Try to upload if we have enough data
              void uploadAccumulatedChunks();
            }
          };

          mediaRecorder.onstop = async () => {
            if (!uploadIdRef.current || !currentSessionId) {
              console.warn("No upload ID or session ID for completion");
              return;
            }

            // Upload any remaining chunks as the final part
            if (pendingChunksRef.current.length > 0) {
              const finalBlob = new Blob(pendingChunksRef.current, { type: mimeType });
              const partNumber = partNumberRef.current;

              try {
                const { upload_url } = await getPartUploadUrl(
                  currentSessionId,
                  uploadIdRef.current,
                  partNumber
                );
                const etag = await uploadPart(upload_url, finalBlob);
                uploadedPartsRef.current.push({ part_number: partNumber, etag });
                console.log(`Uploaded final part ${partNumber} (${(finalBlob.size / 1024 / 1024).toFixed(2)}MB)`);
              } catch (err) {
                console.error("Failed to upload final part:", err);
              }
            }
            // Don't complete the upload here - wait for visibility selection
            console.log("Final part uploaded, waiting for visibility selection...");
          };

          mediaRecorder.start(1000); // Collect data every second
        } catch (recorderError) {
          console.warn("MediaRecorder not supported, video upload will be disabled:", recorderError);
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
      // Stop canvas animation
      if (canvasAnimationRef.current) {
        cancelAnimationFrame(canvasAnimationRef.current);
        canvasAnimationRef.current = null;
      }
      // Stop media recorder
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      // Close recording audio context
      if (recordingAudioContextRef.current) {
        recordingAudioContextRef.current.close();
        recordingAudioContextRef.current = null;
      }
      // Clear canvas refs
      recordingCanvasRef.current = null;
      recordingCtxRef.current = null;
      recordingAudioDestRef.current = null;
      micSourceRef.current = null;
      // Stop media stream tracks
      setStream((current) => {
        current?.getTracks().forEach((track) => track.stop());
        return null;
      });
    };
  }, [phase]);

  const requestPostMortemWithRetry = useCallback(
    async (attempts: number = 6, initialDelayMs: number = 1000) => {
      if (!sessionId) return;
      let lastError: unknown;
      for (let attempt = 0; attempt < attempts; attempt += 1) {
        try {
          await requestPostMortem(sessionId);
          return;
        } catch (error) {
          lastError = error;
          if (attempt < attempts - 1) {
            // For 404 errors (session not found), use longer exponential backoff
            // as the backend may still be processing the session data
            const is404 = error instanceof PostMortemError && error.status === 404;
            const delay = is404
              ? initialDelayMs * Math.pow(2, attempt) // exponential: 1s, 2s, 4s, 8s...
              : initialDelayMs; // constant delay for other errors
            console.log(`Post-mortem attempt ${attempt + 1} failed (${is404 ? "404" : "error"}), retrying in ${delay}ms...`);
            await new Promise((resolve) => window.setTimeout(resolve, delay));
          }
        }
      }
      throw lastError;
    },
    [sessionId]
  );

  /**
   * Wait for the backend to confirm session data is stored.
   * This is triggered when we receive the negotiation_complete WebSocket message.
   */
  const waitForSessionDataStored = useCallback((timeoutMs: number = 10000) => {
    // If already stored, resolve immediately
    if (sessionDataStoredRef.current) {
      return Promise.resolve(true);
    }

    // If WebSocket is not open, we can't wait
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn("WebSocket not open, cannot wait for session data");
      return Promise.resolve(false);
    }

    return new Promise<boolean>((resolve) => {
      const timer = window.setTimeout(() => {
        console.warn("Timeout waiting for session data to be stored");
        if (sessionDataStoredResolveRef.current === resolve) {
          sessionDataStoredResolveRef.current = null;
        }
        resolve(false);
      }, timeoutMs);

      sessionDataStoredResolveRef.current = (value: boolean) => {
        window.clearTimeout(timer);
        sessionDataStoredResolveRef.current = null;
        resolve(value);
      };
    });
  }, []);

  /**
   * Complete post-mortem workflow:
   * 1. Complete S3 upload with visibility setting
   * 2. Get presigned URL from response
   * 3. Update post-mortem with video URL
   * 4. Run post-mortem analysis
   * 5. Navigate to post-mortem page
   */
  const handleVisibilitySelect = useCallback(
    async (isPublic: boolean) => {
      setShowVisibilityDialog(false);
      setIsProcessingPostMortem(true);

      const urlParams = new URLSearchParams(window.location.search);
      const currentSessionId = urlParams.get("sessionId") || sessionId;

      if (!currentSessionId) {
        console.error("No session ID available");
        router.push("/dashboard");
        return;
      }

      try {
        // Step 1: Complete S3 upload with visibility
        setProcessingStatus("Completing video upload...");
        let videoUrl: string | null = null;

        if (uploadIdRef.current && uploadedPartsRef.current.length > 0) {
          console.log("Completing multipart upload with visibility:", isPublic);
          const result = await completeMultipartUpload(
            currentSessionId,
            uploadIdRef.current,
            uploadedPartsRef.current,
            isPublic
          );
          videoUrl = result.video_url;
          console.log("Video upload completed:", videoUrl);

          // Step 2 & 3: Update post-mortem with video URL
          if (videoUrl) {
            setProcessingStatus("Linking video to analysis...");
            try {
              await updatePostMortemVideoUrl(currentSessionId, videoUrl);
              console.log("Video URL linked to post-mortem");
            } catch (err) {
              console.warn("Failed to link video to post-mortem:", err);
            }
          }
        } else {
          console.log("No video parts to upload");
        }

        // Step 4: Run post-mortem analysis
        setProcessingStatus("Analyzing your negotiation...");
        try {
          await requestPostMortemWithRetry();
          console.log("Post-mortem analysis complete");
        } catch (err) {
          console.error("Failed to run post-mortem analysis:", err);
        }

        // Step 5: Navigate to post-mortem page
        setProcessingStatus("Loading your results...");
        router.push(`/postmortem/${currentSessionId}`);
      } catch (err) {
        console.error("Error in post-mortem workflow:", err);
        // Navigate anyway to show whatever analysis we have
        router.push(`/postmortem/${currentSessionId}`);
      }
    },
    [sessionId, router, requestPostMortemWithRetry]
  );

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

  const stopTtsPlayback = useCallback(() => {
    // Stop all queued TTS audio sources
    ttsSourcesRef.current.forEach((source) => {
      try {
        source.stop();
        source.disconnect();
      } catch {
        // Source may have already ended
      }
    });
    ttsSourcesRef.current = [];
    isTtsPlayingRef.current = false;
    ttsQueueEndRef.current = 0;

    // Clear the end timer
    if (ttsEndTimerRef.current) {
      window.clearTimeout(ttsEndTimerRef.current);
      ttsEndTimerRef.current = null;
    }

    // Reset agent status
    setAgentStatus("idle");
    setAgentActivity(0);

    // Notify backend about barge-in
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "barge_in" }));
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
    negotiationCompleteRef.current = false;
    sessionDataStoredRef.current = false;
    sessionDataStoredResolveRef.current = null;
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
          isTtsPlayingRef.current = true;
          ttsStartTimeRef.current = Date.now();
          ttsSourcesRef.current = [];
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
          // Connect to speaker output for playback
          source.connect(context.destination);
          // Also connect to recording destination to capture TTS audio
          if (recordingAudioDestRef.current && recordingAudioContextRef.current) {
            // Create a media stream source from the TTS context and route to recording
            // We need to copy the audio to the recording context
            const recordingCtx = recordingAudioContextRef.current;
            const recordingBuffer = recordingCtx.createBuffer(1, pcm.length, 44100);
            recordingBuffer.copyToChannel(pcm, 0);
            const recordingSource = recordingCtx.createBufferSource();
            recordingSource.buffer = recordingBuffer;
            recordingSource.connect(recordingAudioDestRef.current);
            // Schedule at same relative time
            const recordingStartTime = Math.max(
              recordingCtx.currentTime,
              recordingCtx.currentTime + (Math.max(context.currentTime, ttsQueueEndRef.current) - context.currentTime)
            );
            recordingSource.start(recordingStartTime);
          }
          const startTime = Math.max(
            context.currentTime,
            ttsQueueEndRef.current
          );
          source.start(startTime);
          ttsQueueEndRef.current = startTime + audioBuffer.duration;
          // Track the source for barge-in cancellation
          ttsSourcesRef.current.push(source);
          source.onended = () => {
            ttsSourcesRef.current = ttsSourcesRef.current.filter((s) => s !== source);
          };
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
            isTtsPlayingRef.current = false;
            // If negotiation was completed, stop recording and show visibility dialog
            if (negotiationCompleteRef.current && !autoEndRef.current) {
              autoEndRef.current = true;
              // Stop recording to finalize the upload
              if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
                mediaRecorderRef.current.stop();
              }
              // Show visibility dialog after a brief delay for final upload
              window.setTimeout(() => {
                setShowVisibilityDialog(true);
              }, 500);
            }
          }, remaining * 1000 + 40);
        }
        if (data.type === "negotiation_complete") {
          // Mark negotiation as complete - will show visibility dialog after audio finishes
          negotiationCompleteRef.current = true;
          // Mark that session data has been stored by the backend
          sessionDataStoredRef.current = true;
          // Resolve any pending waitForSessionDataStored promise
          sessionDataStoredResolveRef.current?.(true);
          // Show a brief "Deal closed!" status
          setCoachSuggestions((prev) => [
            {
              id: `deal-${Date.now()}`,
              text: "Deal closed! Preparing your analysis...",
              time: "now",
              priority: "high",
              category: "System",
            },
            ...prev,
          ]);
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
  }, [sessionId, scenario, phase, endCall]);

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

      // Detect if user is speaking (calculate RMS energy)
      let energy = 0;
      for (let i = 0; i < input.length; i += 1) {
        energy += input[i] * input[i];
      }
      const rms = Math.sqrt(energy / input.length);
      const speechThreshold = 0.05;

      // If TTS is playing and user starts speaking, trigger barge-in
      if (isTtsPlayingRef.current && rms > speechThreshold) {
        speechFrameCountRef.current += 1;
      } else {
        speechFrameCountRef.current = 0;
      }
      if (isTtsPlayingRef.current && speechFrameCountRef.current >= 3) {
        const now = Date.now();
        if (now - ttsStartTimeRef.current > 500 && now - lastBargeInRef.current > 1000) {
          lastBargeInRef.current = now;
          stopTtsPlayback();
        }
        speechFrameCountRef.current = 0;
      }

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
  }, [stream, isMuted, socketReady, phase, stopTtsPlayback]);

  const handleEndSession = useCallback(() => {
    autoEndRef.current = true;

    // Stop all tracks
    stream?.getTracks().forEach((track) => track.stop());

    // Stop recording and trigger the onstop handler (uploads final part)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    // Send end_negotiation message to backend - this triggers store_session_data
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: "end_negotiation" }));
    }

    // Wait for backend to confirm session data is stored before showing dialog
    void (async () => {
      await waitForSessionDataStored();
      // Small additional delay for final video part upload
      await new Promise((resolve) => window.setTimeout(resolve, 500));
      setShowVisibilityDialog(true);
    })();
  }, [stream, waitForSessionDataStored]);

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
      // Stop recording and show visibility dialog
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      window.setTimeout(() => {
        setShowVisibilityDialog(true);
      }, 500);
    }
  }, [phase]);

  // Show visibility dialog or processing state
  if (showVisibilityDialog || isProcessingPostMortem) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-night text-white">
        {isProcessingPostMortem ? (
          <div className="text-center">
            <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-olive border-t-transparent" />
            <div className="text-lg font-semibold">{processingStatus || "Processing..."}</div>
            <p className="mt-2 text-sm text-white/60">This may take a few moments</p>
          </div>
        ) : null}
        <VisibilityDialog
          isOpen={showVisibilityDialog}
          onSelect={handleVisibilitySelect}
        />
      </div>
    );
  }

  // When ended but dialog not yet shown, show brief loading
  if (phase === "ended") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-night text-white">
        <div className="text-center">
          <div className="text-lg font-semibold">Preparing...</div>
        </div>
      </div>
    );
  }

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
                onClick={() => setIsSkipConfirmOpen(true)}
                className="rounded-full border border-olive/50 bg-olive/20 px-5 py-3 text-sm font-semibold text-white transition hover:bg-olive/30 cursor-pointer"
              >
                Skip to negotiation
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

        <Dialog open={isSkipConfirmOpen} onClose={() => setIsSkipConfirmOpen(false)} className="relative z-50">
          <div className="fixed inset-0 bg-black/70" aria-hidden="true" />
          <div className="fixed inset-0 flex items-center justify-center p-6">
            <DialogPanel className="w-full max-w-md rounded-2xl border border-white/10 bg-black/90 p-8 text-white shadow-2xl">
              <DialogTitle className="text-xl font-semibold text-white">
                Skip to negotiation?
              </DialogTitle>
              <p className="mt-3 text-sm text-white/70">
                You still have {formatTime(notesRemaining)} left for note-taking. Are you sure you want to start the negotiation now?
              </p>
              <div className="mt-6 flex gap-3">
                <Button
                  type="button"
                  onClick={() => setIsSkipConfirmOpen(false)}
                  className="flex-1 rounded-full border border-white/20 bg-transparent px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10 cursor-pointer"
                >
                  Keep preparing
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setIsSkipConfirmOpen(false);
                    startCall();
                  }}
                  className="flex-1 rounded-full bg-olive px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg cursor-pointer"
                >
                  Start now
                </Button>
              </div>
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
