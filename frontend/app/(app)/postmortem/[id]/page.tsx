import { Navbar } from "@/components/Navbar";
import { fetchPostMortem, type PostMortemResult } from "@/lib/api";
import { PostMortemHeader } from "./PostMortemHeader";
import { PostMortemScore } from "./PostMortemScore";
import { PostMortemPanels } from "./PostMortemPanels";
import { PostMortemMoments } from "./PostMortemMoments";
import { PostMortemMetrics } from "./PostMortemMetrics";

const fallbackAnalysis: PostMortemResult = {
  overallScore: 85,
  strengths: [
    "Established credibility early with well-researched data points and clear understanding of market conditions",
    "Demonstrated strong active listening skills and adapted communication style to match the opponent's approach",
    "Used strategic pauses effectively to create space for reflection and demonstrate confidence in your position",
  ],
  improvements: [
    "Could have asked more clarifying questions in the first 10 minutes to better understand underlying priorities",
    "Missed opportunity to anchor the conversation earlier with your initial offer or position",
    "Speaking pace was slightly rushed during critical moments. Slow down to project more confidence",
  ],
  metrics: [
    { label: "Communication", score: 88, change: 5 },
    { label: "Strategy", score: 82, change: 3 },
    { label: "Persuasion", score: 86, change: 7 },
    { label: "Listening", score: 79, change: -2 },
    { label: "Confidence", score: 91, change: 4 },
    { label: "Adaptability", score: 83, change: 6 },
  ],
  keyMoments: [
    { time: "3:42", desc: "Excellent rapport building through mirroring and active listening techniques", type: "positive" },
    { time: "8:15", desc: "Strong counter-offer presentation supported by market data and clear reasoning", type: "positive" },
    { time: "12:30", desc: "Missed chance to ask clarifying questions about their underlying interests", type: "negative" },
    { time: "16:45", desc: "Strategic concession effectively moved the conversation toward mutual agreement", type: "positive" },
  ],
};

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function PostMortemPage({ params }: PageProps) {
  const { id } = await params;

  let analysis = fallbackAnalysis;
  let usedFallback = false;

  try {
    analysis = await fetchPostMortem(id);
  } catch (error) {
    console.error("Failed to fetch post-mortem analysis:", error);
    usedFallback = true;
    analysis = fallbackAnalysis;
  }

  return (
    <div className="min-h-screen bg-white">
      <Navbar currentPage="dashboard" />

      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 pb-20 pt-12">
        <PostMortemHeader />
        {usedFallback && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            Analysis is still being generated. Showing sample results. Refresh the page in a few moments.
          </div>
        )}
        <PostMortemScore score={analysis.overallScore} />
        <PostMortemPanels strengths={analysis.strengths} improvements={analysis.improvements} />
        <PostMortemMoments moments={analysis.keyMoments} />
        <PostMortemMetrics metrics={analysis.metrics} />
      </div>
    </div>
  );
}
