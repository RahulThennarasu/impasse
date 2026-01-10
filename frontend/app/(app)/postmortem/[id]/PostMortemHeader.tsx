import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export function PostMortemHeader() {
  return (
    <div>
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-2 rounded-md border border-black/10 px-3 py-2 text-xs font-semibold text-[#666] transition hover:border-black/20 hover:bg-black/5 hover:text-[#1a1a1a]"
      >
        <ArrowLeft size={14} />
        Back to Dashboard
      </Link>
      <h1 className="mt-5 text-3xl font-serif text-[#1a1a1a]">Session Analysis</h1>
      <p className="mt-2 text-sm text-[#666]">Detailed performance review with AI-powered insights.</p>
    </div>
  );
}
