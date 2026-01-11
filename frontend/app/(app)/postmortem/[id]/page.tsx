import { Navbar } from "@/components/Navbar";
import { fetchAnalytics, getVideoDownloadUrl } from "@/lib/api";
import { PostMortemHeader } from "./PostMortemHeader";
import { PostMortemScore } from "./PostMortemScore";
import { PostMortemPanels } from "./PostMortemPanels";
import { PostMortemMoments } from "./PostMortemMoments";
import { PostMortemMetrics } from "./PostMortemMetrics";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function PostMortemPage({ params }: PageProps) {
  const { id } = await params;

  const analysis = await fetchAnalytics(id);
  let videoUrl: string | null = null;

  try {
    const { download_url } = await getVideoDownloadUrl(id);
    videoUrl = download_url;
  } catch (error) {
    console.error("Failed to fetch video download URL:", error);
  }

  return (
    <div className="min-h-screen bg-white">
      <Navbar currentPage="dashboard" />

      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 pb-20 pt-12">
        <PostMortemHeader />
        {videoUrl && (
          <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
              Session recording
            </div>
            <video
              className="mt-3 w-full rounded-xl bg-black"
              controls
              preload="metadata"
            >
              <source src={videoUrl} type="video/webm" />
              Your browser does not support the video tag.
            </video>
          </section>
        )}
        <PostMortemScore score={analysis.overallScore} />
        <PostMortemPanels strengths={analysis.strengths} improvements={analysis.improvements} />
        <PostMortemMoments moments={analysis.keyMoments} />
        <PostMortemMetrics metrics={analysis.metrics} />
      </div>
    </div>
  );
}
