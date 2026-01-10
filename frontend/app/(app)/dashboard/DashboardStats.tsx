import { Clock, Target, TrendingUp } from "lucide-react";

const stats = [
  {
    label: "Average Score",
    value: "82",
    subtext: "+15% from last month",
    icon: Target,
  },
  {
    label: "Sessions",
    value: "24",
    subtext: "Total practice sessions",
    icon: TrendingUp,
  },
  {
    label: "Practice Time",
    value: "18h",
    subtext: "+2h this week",
    icon: Clock,
  },
];

export function DashboardStats() {
  return (
    <section className="mx-auto -mt-10 max-w-6xl px-6 lg:max-w-[1400px]">
      <div className="grid gap-6 lg:grid-cols-3">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          const clipClass = index % 2 === 0 ? "clip-card-a" : "clip-card-b";
          return (
            <div key={stat.label} className={`bg-[#7fb069] p-[3px] ${clipClass}`}>
              <div className={`relative bg-white p-10 ${clipClass}`}>
                <div className="absolute right-6 top-6 flex h-12 w-12 items-center justify-center bg-[#7fb069]/10 text-[#7fb069] clip-hex">
                  <Icon size={22} />
                </div>
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#7fb069]">
                  {stat.label}
                </div>
                <div className="mt-4 text-5xl font-serif text-[#1a1a1a]">
                  {stat.value}
                </div>
                <div className="mt-3 text-sm font-semibold text-[#7fb069]">
                  {stat.subtext}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
