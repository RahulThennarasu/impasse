"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useSearchParams } from "next/navigation";
import type { ScenarioContext } from "@/lib/api";

const NOTES_DURATION_SECONDS = 15 * 60;
const CALL_DURATION_SECONDS = 15 * 60;

type NegotiationPhase = "notes" | "ready" | "call" | "ended";

type NegotiationState = {
  scenario: ScenarioContext | null;
  notes: string;
  phase: NegotiationPhase;
  notesStartedAt: number | null;
  callStartedAt: number | null;
};

type NegotiationContextValue = {
  sessionId: string;
  scenario: ScenarioContext | null;
  notes: string;
  phase: NegotiationPhase;
  notesRemaining: number;
  callRemaining: number;
  notesStartedAt: number | null;
  callStartedAt: number | null;
  setNotes: (value: string) => void;
  setScenario: (value: ScenarioContext | null) => void;
  startCall: () => void;
  markCallStarted: () => void;
  endCall: () => void;
  setNotesRemaining: (seconds: number) => void;
};

const NegotiationContext = createContext<NegotiationContextValue | null>(null);

const getStorageKey = (sessionId: string) => `negotiation:${sessionId}`;

export function NegotiationProvider({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("sessionId") ?? "";
  const [state, setState] = useState<NegotiationState>({
    scenario: null,
    notes: "",
    phase: "notes",
    notesStartedAt: null,
    callStartedAt: null,
  });
  const [now, setNow] = useState(() => Date.now());
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    if (!sessionId || typeof window === "undefined") return;
    const storageKey = getStorageKey(sessionId);
    const stored = window.localStorage.getItem(storageKey);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as NegotiationState;
        setState({
          scenario: parsed.scenario ?? null,
          notes: parsed.notes ?? "",
          phase: parsed.phase ?? "notes",
          notesStartedAt: parsed.notesStartedAt ?? Date.now(),
          callStartedAt: parsed.callStartedAt ?? null,
        });
      } catch {
        setState({
          scenario: null,
          notes: "",
          phase: "notes",
          notesStartedAt: Date.now(),
          callStartedAt: null,
        });
      }
    } else {
      setState((prev) => ({
        ...prev,
        phase: "notes",
        notesStartedAt: prev.notesStartedAt ?? Date.now(),
      }));
    }

    const scenarioStored = window.sessionStorage.getItem(`scenario:${sessionId}`);
    if (scenarioStored) {
      try {
        const scenarioParsed = JSON.parse(scenarioStored) as ScenarioContext;
        setState((prev) => ({
          ...prev,
          scenario: prev.scenario ?? scenarioParsed,
        }));
      } catch {
        // ignore
      }
    }

    window.localStorage.setItem("negotiation:active", sessionId);
    setHydrated(true);
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId || !hydrated || typeof window === "undefined") return;
    const storageKey = getStorageKey(sessionId);
    window.localStorage.setItem(storageKey, JSON.stringify(state));
  }, [sessionId, state, hydrated]);

  useEffect(() => {
    if (!sessionId) return;
    const interval = window.setInterval(() => {
      setNow(Date.now());
    }, 1000);
    return () => {
      window.clearInterval(interval);
    };
  }, [sessionId]);

  const notesRemaining = useMemo(() => {
    if (!state.notesStartedAt) return NOTES_DURATION_SECONDS;
    const elapsed = Math.floor((now - state.notesStartedAt) / 1000);
    return Math.max(0, NOTES_DURATION_SECONDS - elapsed);
  }, [now, state.notesStartedAt]);

  const callRemaining = useMemo(() => {
    if (!state.callStartedAt) return CALL_DURATION_SECONDS;
    const elapsed = Math.floor((now - state.callStartedAt) / 1000);
    return Math.max(0, CALL_DURATION_SECONDS - elapsed);
  }, [now, state.callStartedAt]);

  useEffect(() => {
    if (state.phase === "notes" && notesRemaining === 0) {
      setState((prev) => ({ ...prev, phase: "ready" }));
    }
  }, [state.phase, notesRemaining]);

  useEffect(() => {
    if (state.phase === "call" && state.callStartedAt && callRemaining === 0) {
      setState((prev) => ({ ...prev, phase: "ended" }));
    }
  }, [state.phase, state.callStartedAt, callRemaining]);

  const setNotes = useCallback((value: string) => {
    setState((prev) => ({ ...prev, notes: value }));
  }, []);

  const setScenario = useCallback((value: ScenarioContext | null) => {
    setState((prev) => ({ ...prev, scenario: value }));
  }, []);

  const startCall = useCallback(() => {
    setState((prev) => ({ ...prev, phase: "call" }));
  }, []);

  const markCallStarted = useCallback(() => {
    setState((prev) =>
      prev.callStartedAt
        ? prev
        : {
            ...prev,
            callStartedAt: Date.now(),
          }
    );
  }, []);

  const endCall = useCallback(() => {
    setState((prev) => ({ ...prev, phase: "ended" }));
  }, []);

  const setNotesRemaining = useCallback((seconds: number) => {
    const clamped = Math.max(0, Math.min(NOTES_DURATION_SECONDS, seconds));
    setState((prev) => ({
      ...prev,
      notesStartedAt: Date.now() - (NOTES_DURATION_SECONDS - clamped) * 1000,
    }));
  }, []);

  const value = useMemo<NegotiationContextValue>(
    () => ({
      sessionId,
      scenario: state.scenario,
      notes: state.notes,
      phase: state.phase,
      notesRemaining,
      callRemaining,
      notesStartedAt: state.notesStartedAt,
      callStartedAt: state.callStartedAt,
      setNotes,
      setScenario,
      startCall,
      markCallStarted,
      endCall,
      setNotesRemaining,
    }),
    [
      sessionId,
      state.scenario,
      state.notes,
      state.phase,
      state.notesStartedAt,
      state.callStartedAt,
      notesRemaining,
      callRemaining,
      setNotes,
      setScenario,
      startCall,
      markCallStarted,
      endCall,
      setNotesRemaining,
    ]
  );

  return <NegotiationContext.Provider value={value}>{children}</NegotiationContext.Provider>;
}

export function useNegotiation() {
  const context = useContext(NegotiationContext);
  if (!context) {
    throw new Error("useNegotiation must be used within NegotiationProvider");
  }
  return context;
}
