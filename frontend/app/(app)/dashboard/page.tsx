import { Navbar } from "@/components/Navbar";
import { DashboardHero } from "./DashboardHero";
import { DashboardStats } from "./DashboardStats";
import { RecentSessions } from "./RecentSessions";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-hero-gradient">
      <Navbar currentPage="dashboard" />
      <DashboardHero />
      <DashboardStats />
      <RecentSessions />
    </div>
  );
}
