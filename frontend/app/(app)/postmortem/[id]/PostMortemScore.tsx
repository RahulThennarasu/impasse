import { TrendingUp } from "lucide-react";

type PostMortemScoreProps = {
  score: number;
};

export function PostMortemScore({ score }: PostMortemScoreProps) {
  return (
    <div className="rounded-2xl border border-strong bg-subtle p-10 text-center">
      <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">Overall Performance</div>
      <div className="mt-4 text-6xl font-serif text-ink">{score}</div>
      <div className="mt-4 flex items-center justify-center gap-3 text-sm text-muted">
        <span className="flex items-center gap-2 rounded-full bg-olive-soft px-3 py-1 text-xs font-semibold text-ink">
          <TrendingUp size={14} />
          +7 points
        </span>
        from your last session
      </div>
    </div>
  );
}
