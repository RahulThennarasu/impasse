import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-b from-[#e8f5e1] to-[#f5faf3]">
      <div className="pattern-grid absolute inset-0 opacity-70" />

      <nav className="relative z-10 flex items-center justify-between px-6 py-8 lg:px-12">
        <div className="relative text-2xl font-serif text-[#1a1a1a]">
          impasse
          <span className="absolute bottom-0 left-0 h-[3px] w-10 bg-[#7fb069]" />
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/signin"
            className="rounded-full border-2 border-black/10 bg-white px-6 py-3 text-sm font-semibold text-[#1a1a1a] transition hover:border-black/20 hover:bg-black/5"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            className="rounded-full bg-[#1a1a1a] px-6 py-3 text-sm font-bold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
          >
            Sign up
          </Link>
        </div>
      </nav>

      <main className="relative z-10 flex min-h-[calc(100vh-140px)] items-center justify-center px-6">
        <div className="max-w-4xl text-center">
          <h1 className="text-balance text-5xl font-serif leading-[1.05] text-[#1a1a1a] sm:text-6xl lg:text-[6rem]">
            master negotiation through practice
          </h1>
          <div className="mx-auto mt-8 h-1 w-40 bg-[#7fb069]" />
          <p className="mx-auto mt-8 max-w-2xl text-lg text-[#666] sm:text-xl">
            Train with AI opponents, get real-time coaching, and analyze your performance with detailed post-mortems.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/signup"
              className="rounded-full bg-[#1a1a1a] px-8 py-4 text-base font-bold text-white shadow-lg transition hover:-translate-y-1 hover:shadow-xl"
            >
              Start practicing
            </Link>
            <Link
              href="/library"
              className="rounded-full border-2 border-black/10 bg-white px-8 py-4 text-base font-semibold text-[#1a1a1a] transition hover:border-black/20 hover:bg-black/5"
            >
              Explore sessions
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
