import Link from "next/link";
import { SignInForm } from "./SignInForm";

export default function SignInPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-b from-[#c5e5b4] via-[#e8f5e1] to-white">
      <div className="pointer-events-none absolute left-[10%] top-[10%] h-[320px] w-[320px] rounded-full bg-[radial-gradient(circle,rgba(168,217,159,0.25)_0%,transparent_70%)] blur-3xl" />
      <div className="pointer-events-none absolute right-[20%] top-[40%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle,rgba(127,176,105,0.2)_0%,transparent_70%)] blur-[100px]" />

      <nav className="relative z-10 flex items-center justify-between px-6 py-7 lg:px-12">
        <div className="text-2xl font-serif text-[#1a1a1a]">impasse</div>
        <Link
          href="/signup"
          className="rounded-md bg-[#7fb069] px-5 py-2 text-sm font-semibold text-white transition hover:-translate-y-0.5"
        >
          Sign up
        </Link>
      </nav>

      <main className="relative z-10 flex min-h-[calc(100vh-140px)] items-center justify-center px-6">
        <div className="w-full max-w-md text-center">
          <h1 className="text-4xl font-serif text-[#1a1a1a] sm:text-5xl">Welcome back</h1>
          <p className="mt-4 text-base text-[#666]">Sign in to continue your practice</p>

          <div className="glass-panel mt-10 rounded-xl border border-white/80 p-8 text-left shadow-[0_4px_24px_rgba(0,0,0,0.06)]">
            <SignInForm />
            <div className="mt-6 text-center text-sm text-[#666]">
              New here?{" "}
              <Link href="/signup" className="font-semibold text-[#1a1a1a]">
                Create an account
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
