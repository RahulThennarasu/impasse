import { TrendingDown, TrendingUp } from "lucide-react";

type Metric = {
  label: string;
  score: number;
  change: number;
};

type PostMortemMetricsProps = {
  metrics: Metric[];
};

export function PostMortemMetrics({ metrics }: PostMortemMetricsProps) {
  return (
    <div className="rounded-2xl border border-strong bg-white p-8">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-serif text-ink">Skill breakdown</h3>
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">delta</span>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-xl border border-strong px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-ink">{metric.label}</span>
              <span className="text-xs font-semibold text-muted">{metric.score}</span>
            </div>
            <div className="mt-3 h-2 w-full rounded-full bg-subtle">
              <div
                className="h-2 rounded-full bg-olive"
                style={{ width: `${metric.score}%` }}
              />
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-muted">
              {metric.change >= 0 ? (
                <TrendingUp size={12} className="text-olive" />
              ) : (
                <TrendingDown size={12} className="text-danger-muted" />
              )}
              {metric.change >= 0 ? "+" : ""}
              {metric.change} pts
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
