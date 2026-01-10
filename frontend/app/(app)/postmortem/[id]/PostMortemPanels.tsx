import { Target, TrendingUp } from "lucide-react";

type PostMortemPanelsProps = {
  strengths: string[];
  improvements: string[];
};

export function PostMortemPanels({ strengths, improvements }: PostMortemPanelsProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-2xl border border-[#e8e8e8] bg-white p-8">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-[#f5faf3]">
            <TrendingUp size={18} />
          </span>
          <div>
            <h3 className="text-lg font-serif text-[#1a1a1a]">Strengths</h3>
            <p className="text-xs text-[#999]">What you did well</p>
          </div>
        </div>
        <div className="mt-6 space-y-3">
          {strengths.map((strength) => (
            <div
              key={strength}
              className="rounded-md border-l-2 border-[#1a1a1a] bg-[#f5faf3] px-4 py-3 text-sm text-[#1a1a1a]"
            >
              {strength}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-[#e8e8e8] bg-white p-8">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-[#f5faf3]">
            <Target size={18} />
          </span>
          <div>
            <h3 className="text-lg font-serif text-[#1a1a1a]">Growth Areas</h3>
            <p className="text-xs text-[#999]">Focus for next time</p>
          </div>
        </div>
        <div className="mt-6 space-y-3">
          {improvements.map((improvement) => (
            <div
              key={improvement}
              className="rounded-md border-l-2 border-[#999] bg-[#f5faf3] px-4 py-3 text-sm text-[#1a1a1a]"
            >
              {improvement}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
