"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createScenarioContext, createVideoSession, type ScenarioContext } from "@/lib/api";

export function ScenarioForm() {
  const router = useRouter();
  const [keywords, setKeywords] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenario, setScenario] = useState<ScenarioContext | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await createScenarioContext(keywords.trim());
      setScenario(result);
    } catch (err) {
      setError("Unable to generate scenario. Try different keywords.");
    } finally {
      setLoading(false);
    }
  };

  const handleStart = () => {
    if (!scenario) return;
    const agentId = scenario.agent_id ?? "opponent";
    createVideoSession("pending")
      .then((videoSession) => {
        const sessionId = videoSession.session_id;
        sessionStorage.setItem(`scenario:${sessionId}`, JSON.stringify(scenario));
        router.push(`/negotiation?sessionId=${sessionId}&agentId=${agentId}`);
      })
      .catch(() => {
        setError("Unable to create session. Try again.");
      });
  };

  return (
    <div className="glass-panel mx-auto max-w-3xl rounded-2xl border border-white/80 p-10">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="text-sm font-semibold text-ink">Scenario keywords</label>
          <textarea
            value={keywords}
            onChange={(event) => setKeywords(event.target.value)}
            placeholder="Salary negotiation, equity, remote work, timeline pressure..."
            className="mt-3 h-28 w-full resize-none rounded-lg border border-black/10 bg-white p-4 text-sm text-ink outline-none focus-border-olive"
            required
          />
        </div>
        {error ? <p className="text-sm text-danger-muted">{error}</p> : null}
        <button
          type="submit"
          className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
          disabled={loading}
        >
          {loading ? "Generating..." : "Generate scenario"}
        </button>
      </form>

      {scenario ? (
        <div className="mt-10 rounded-2xl border border-strong bg-subtle p-6">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-olive">
            Scenario ready
          </div>
          <h2 className="mt-3 text-3xl font-serif text-ink">{scenario.title}</h2>
          <p className="mt-2 text-sm text-muted">Role: {scenario.role}</p>
          <p className="mt-4 text-sm text-ink">{scenario.description}</p>
          <button
            type="button"
            onClick={handleStart}
            className="mt-6 rounded-full bg-olive px-6 py-3 text-sm font-semibold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
          >
            Enter practice
          </button>
        </div>
      ) : null}
    </div>
  );
}
