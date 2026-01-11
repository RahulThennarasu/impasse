export type ScenarioContext = {
  title: string;
  role: string;
  description: string;
  agent_id?: string;
};

export type CoachTip = {
  id: string;
  text: string;
  time: string;
  priority: "high" | "medium" | "low";
  category: string;
};

export type PostMortemMetric = {
  label: string;
  score: number;
  change: number;
};

export type PostMortemMoment = {
  time: string;
  desc: string;
  type: "positive" | "negative";
};

export type PostMortemResult = {
  overallScore: number;
  strengths: string[];
  improvements: string[];
  metrics: PostMortemMetric[];
  keyMoments: PostMortemMoment[];
};

const DEFAULT_API_BASE = "http://localhost:8000";

const getApiBaseUrl = () =>
  process.env.NEXT_PUBLIC_API_BASE_URL ?? `${DEFAULT_API_BASE}/api/v1`;

const getServerApiBaseUrl = () => process.env.API_BASE_URL ?? getApiBaseUrl();

export const getWsBaseUrl = () => {
  const base = process.env.NEXT_PUBLIC_WS_BASE_URL ?? DEFAULT_API_BASE;
  const normalized = base.replace(/\/$/, "");
  return normalized.replace(/^http/, "ws");
};

export async function createScenarioContext(keywords: string) {
  const response = await fetch(`${getApiBaseUrl()}/scenario_context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ keywords }),
  });

  if (!response.ok) {
    throw new Error("Scenario context request failed");
  }

  return (await response.json()) as ScenarioContext;
}

export async function requestPostMortem(sessionId: string) {
  const response = await fetch(`${getApiBaseUrl()}/post_mortem`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error("Post-mortem request failed");
  }

  return response.json();
}

export async function fetchPostMortem(sessionId: string) {
  const response = await fetch(
    `${getServerApiBaseUrl()}/post_mortem/${sessionId}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Post-mortem fetch failed");
  }

  return (await response.json()) as PostMortemResult;
}
