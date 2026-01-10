import Link from "next/link";
import { SignUpForm } from "./SignUpForm";

export default function SignupPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-b from-[#c5e5b4] via-[#e8f5e1] to-white">
      <div className="pointer-events-none absolute left-[10%] top-[5%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle,rgba(168,217,159,0.3)_0%,transparent_70%)] blur-[100px]" />
      <div className="pointer-events-none absolute right-[15%] top-[50%] h-[320px] w-[320px] rounded-full bg-[radial-gradient(circle,rgba(127,176,105,0.25)_0%,transparent_70%)] blur-[90px]" />
      <div className="pointer-events-none absolute bottom-[10%] left-[25%] h-[280px] w-[280px] rounded-full bg-[radial-gradient(circle,rgba(197,229,180,0.25)_0%,transparent_70%)] blur-[80px]" />

      <nav className="relative z-10 flex items-center justify-between px-6 py-7 lg:px-12">
        <div className="text-2xl font-serif text-[#1a1a1a]">impasse</div>
        <Link
          href="/signin"
          className="rounded-md bg-[#7fb069] px-5 py-2 text-sm font-semibold text-white transition hover:-translate-y-0.5"
        >
          Sign in
        </Link>
      </nav>

      <main className="relative z-10 flex min-h-[calc(100vh-140px)] items-center justify-center px-6 py-10">
        <div className="w-full max-w-lg text-center">
          <h1 className="text-4xl font-serif text-[#1a1a1a] sm:text-5xl">Master the art of negotiation</h1>
          <p className="mt-4 text-base text-[#666]">Practice with AI opponents and get real-time coaching</p>

          <div className="glass-panel mt-10 rounded-xl border border-white/80 p-8 text-left shadow-[0_4px_24px_rgba(0,0,0,0.06)]">
            <SignUpForm />
            <div className="mt-6 text-center text-sm text-[#666]">
              Already have an account?{" "}
              <Link href="/signin" className="font-semibold text-[#1a1a1a]">
                Sign in
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
