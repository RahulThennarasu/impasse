import { Navbar } from "@/components/Navbar";
import { ScenarioForm } from "./ScenarioForm";

export default function PracticePage() {
  return (
    <div className="min-h-screen bg-hero-gradient">
      <Navbar currentPage="dashboard" />
      <section className="relative overflow-hidden px-6 pb-24 pt-20">
        <div className="pattern-grid absolute inset-0" />
        <div className="relative z-10 mx-auto max-w-5xl text-center">
          <h1 className="text-5xl font-serif leading-none text-ink sm:text-6xl">
            Build your scenario
          </h1>
          <div className="mx-auto mt-4 h-1 w-24 bg-olive" />
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted">
            Enter a few keywords and let the scenario generator craft the negotiation setup.
          </p>
        </div>
      </section>
      <section className="px-6 pb-20">
        <ScenarioForm />
      </section>
    </div>
  );
}
