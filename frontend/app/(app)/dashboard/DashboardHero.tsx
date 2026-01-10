export function DashboardHero() {
  return (
    <section className="relative overflow-hidden px-6 pb-24 pt-20">
      <div className="pattern-grid absolute inset-0" />
      <div className="relative z-10 mx-auto max-w-6xl lg:max-w-[1400px]">
        <h1 className="text-5xl font-serif leading-none text-[#1a1a1a] sm:text-6xl lg:text-[5rem]">
          dashboard
        </h1>
        <div className="mt-4 h-1 w-28 bg-[#7fb069]" />
        <p className="mt-6 max-w-xl text-lg text-[#666]">
          Track your journey and continue improving.
        </p>
      </div>
    </section>
  );
}
