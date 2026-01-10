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
    <div className="rounded-2xl border border-[#e8e8e8] bg-white p-8">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-serif text-[#1a1a1a]">Skill breakdown</h3>
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#666]">delta</span>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-xl border border-[#e8e8e8] px-4 py-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-[#1a1a1a]">{metric.label}</span>
              <span className="text-xs font-semibold text-[#666]">{metric.score}</span>
            </div>
            <div className="mt-3 h-2 w-full rounded-full bg-[#f5faf3]">
              <div
                className="h-2 rounded-full bg-[#7fb069]"
                style={{ width: `${metric.score}%` }}
              />
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-[#666]">
              {metric.change >= 0 ? (
                <TrendingUp size={12} className="text-[#7fb069]" />
              ) : (
                <TrendingDown size={12} className="text-[#c26d6d]" />
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
