import { TrendingUp } from "lucide-react";

type PostMortemScoreProps = {
  score: number;
};

export function PostMortemScore({ score }: PostMortemScoreProps) {
  return (
    <div className="rounded-2xl border border-[#e8e8e8] bg-[#f5faf3] p-10 text-center">
      <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#666]">Overall Performance</div>
      <div className="mt-4 text-6xl font-serif text-[#1a1a1a]">{score}</div>
      <div className="mt-4 flex items-center justify-center gap-3 text-sm text-[#666]">
        <span className="flex items-center gap-2 rounded-full bg-[#c5e5b4] px-3 py-1 text-xs font-semibold text-[#1a1a1a]">
          <TrendingUp size={14} />
          +7 points
        </span>
        from your last session
      </div>
    </div>
  );
}
