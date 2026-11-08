import type { Metadata } from "next";
import SitePage from "../components/SitePage";
import TrialCalculator from "../components/TrialCalculator";

export const metadata: Metadata = {
  title: "Trial Calculation — When Does Your Degree Pay Back?",
  description: "Pick a country and career, enter tuition and see payback, 10-year ROI and three salary scenarios from live salary data for Poland and Ukraine. No account needed.",
  alternates: { canonical: "/try" },
};

export default function TryPage() {
  return (
    <SitePage
      kicker="Fence / trial calculation"
      title={<>When does your degree <span className="site-mark">pay you back?</span></>}
      lead="No account needed. Pick a country and a career, set tuition and study length, and Fence runs the same calculation as in the workspace on real salary data."
    >
      <section className="site-section site-section--play" aria-label="Trial calculation">
        <TrialCalculator />
      </section>
    </SitePage>
  );
}
