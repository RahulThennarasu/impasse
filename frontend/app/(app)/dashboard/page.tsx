import { Navbar } from "@/components/Navbar";
import { DashboardHero } from "./DashboardHero";
import { DashboardStats } from "./DashboardStats";
import { RecentSessions } from "./RecentSessions";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#e8f5e1] to-[#f5faf3]">
      <Navbar currentPage="dashboard" />
      <DashboardHero />
      <DashboardStats />
      <RecentSessions />
    </div>
  );
}
