import { Target, TrendingUp } from "lucide-react";

type PostMortemPanelsProps = {
  strengths: string[];
  improvements: string[];
};

export function PostMortemPanels({ strengths, improvements }: PostMortemPanelsProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-2xl border border-strong bg-white p-8">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-subtle">
            <TrendingUp size={18} />
          </span>
          <div>
            <h3 className="text-lg font-serif text-ink">Strengths</h3>
            <p className="text-xs text-muted-strong">What you did well</p>
          </div>
        </div>
        <div className="mt-6 space-y-3">
          {strengths.map((strength) => (
            <div
              key={strength}
              className="rounded-md border-l-2 border-ink bg-subtle px-4 py-3 text-sm text-ink"
            >
              {strength}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-strong bg-white p-8">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-subtle">
            <Target size={18} />
          </span>
          <div>
            <h3 className="text-lg font-serif text-ink">Growth Areas</h3>
            <p className="text-xs text-muted-strong">Focus for next time</p>
          </div>
        </div>
        <div className="mt-6 space-y-3">
          {improvements.map((improvement) => (
            <div
              key={improvement}
              className="rounded-md border-l-2 border-muted-strong bg-subtle px-4 py-3 text-sm text-ink"
            >
              {improvement}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
