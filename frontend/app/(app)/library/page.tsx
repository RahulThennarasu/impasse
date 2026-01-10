import { Navbar } from "@/components/Navbar";
import { LibraryClient } from "./LibraryClient";
import { LibraryHero } from "./LibraryHero";

export default function LibraryPage() {
  return (
    <div className="min-h-screen bg-hero-gradient">
      <Navbar currentPage="library" />
      <LibraryHero />
      <LibraryClient />
    </div>
  );
}
