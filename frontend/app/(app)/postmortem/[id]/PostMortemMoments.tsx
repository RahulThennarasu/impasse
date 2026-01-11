import { MessageSquare, TrendingDown, TrendingUp } from "lucide-react";

type Moment = {
  time: string;
  desc: string;
  type: "positive" | "negative";
};

type PostMortemMomentsProps = {
  moments: Moment[];
};

export function PostMortemMoments({ moments }: PostMortemMomentsProps) {
  return (
    <div className="rounded-2xl border border-strong bg-white p-8">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-md bg-subtle">
          <MessageSquare size={18} />
        </span>
        <div>
          <h3 className="text-lg font-serif text-ink">Key moments</h3>
          <p className="text-xs text-muted-strong">Where the negotiation shifted</p>
        </div>
      </div>
      <div className="mt-6 space-y-3">
        {moments.map((moment, index) => (
          <div
            key={`${moment.time}-${index}`}
            className="flex items-center justify-between rounded-xl border border-strong px-4 py-3"
          >
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-olive">
                {moment.time}
              </div>
              <div className="mt-2 text-sm text-ink">{moment.desc}</div>
            </div>
            <div className="flex items-center gap-2 text-xs font-semibold">
              {moment.type === "positive" ? (
                <span className="flex items-center gap-1 rounded-full bg-olive-soft px-3 py-1 text-ink">
                  <TrendingUp size={12} />
                  Positive
                </span>
              ) : (
                <span className="flex items-center gap-1 rounded-full bg-danger-soft px-3 py-1 text-ink">
                  <TrendingDown size={12} />
                  Watch out
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
