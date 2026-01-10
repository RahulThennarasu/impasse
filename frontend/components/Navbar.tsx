import Link from "next/link";
import { LayoutDashboard, Library, LogOut, Play } from "lucide-react";

type NavbarProps = {
  currentPage?: "dashboard" | "library" | "postmortem";
};

export function Navbar({ currentPage }: NavbarProps) {
  const navItems = [
    { label: "Dashboard", href: "/dashboard", key: "dashboard", icon: LayoutDashboard },
    { label: "Library", href: "/library", key: "library", icon: Library },
  ] as const;

  return (
    <nav className="sticky top-0 z-50 border-b-[3px] border-olive bg-surface-85 backdrop-blur-[30px]">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5 lg:max-w-[1400px]">
        <div className="flex items-center gap-10">
          <Link href="/dashboard" className="relative text-2xl font-serif text-ink">
            impasse
            <span className="absolute bottom-0 left-0 h-[3px] w-10 bg-olive" />
          </Link>
          <div className="hidden items-center gap-2 md:flex">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = currentPage === item.key;
              return (
                <Link
                  key={item.key}
                  href={item.href}
                  className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition ${
                    active
                      ? "bg-ink text-white"
                      : "border-2 border-black/10 text-muted hover:border-black/20 hover:bg-black/5"
                  }`}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/negotiation"
            className="flex items-center gap-2 rounded-full bg-ink px-6 py-3 text-sm font-bold text-white shadow-md transition hover:-translate-y-0.5 hover:shadow-lg"
          >
            <Play size={14} />
            Start Practice
          </Link>
          <button
            type="button"
            className="flex h-11 w-11 items-center justify-center rounded-full border-2 border-black/10 bg-white text-muted transition hover:border-black/20 hover:bg-black/5 hover:text-ink"
            aria-label="Log out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </nav>
  );
}
