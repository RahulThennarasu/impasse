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
    <div className="rounded-2xl border border-[#e8e8e8] bg-white p-8">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-md bg-[#f5faf3]">
          <MessageSquare size={18} />
        </span>
        <div>
          <h3 className="text-lg font-serif text-[#1a1a1a]">Key moments</h3>
          <p className="text-xs text-[#999]">Where the negotiation shifted</p>
        </div>
      </div>
      <div className="mt-6 space-y-3">
        {moments.map((moment) => (
          <div
            key={moment.time}
            className="flex items-center justify-between rounded-xl border border-[#e8e8e8] px-4 py-3"
          >
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#7fb069]">
                {moment.time}
              </div>
              <div className="mt-2 text-sm text-[#1a1a1a]">{moment.desc}</div>
            </div>
            <div className="flex items-center gap-2 text-xs font-semibold">
              {moment.type === "positive" ? (
                <span className="flex items-center gap-1 rounded-full bg-[#c5e5b4] px-3 py-1 text-[#1a1a1a]">
                  <TrendingUp size={12} />
                  Positive
                </span>
              ) : (
                <span className="flex items-center gap-1 rounded-full bg-[#f4d2d2] px-3 py-1 text-[#1a1a1a]">
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
