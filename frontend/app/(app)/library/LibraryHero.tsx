export function LibraryHero() {
  return (
    <section className="relative overflow-hidden px-6 pb-24 pt-20">
      <div className="pattern-grid absolute inset-0" />
      <div className="relative z-10 mx-auto max-w-6xl lg:max-w-[1400px]">
        <h1 className="text-5xl font-serif leading-none text-ink sm:text-6xl lg:text-[5rem]">
          library
        </h1>
        <div className="mt-4 h-1 w-24 bg-olive" />
        <p className="mt-6 max-w-xl text-lg text-muted">
          Learn from top performers and discover new strategies.
        </p>
      </div>
    </section>
  );
}
