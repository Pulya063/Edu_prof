/** Plan catalogue shared by the pricing page and its structured data. */
export type Plan = {
  id: string;
  name: string;
  description: string;
  priceMonthly: string;
  priceYearly: string;
  featuresLabel: string;
  features: string[];
  badge?: string;
};

export const PLANS: Plan[] = [
  { id: "pro", name: "Pro", description: "For one person comparing education and career paths", priceMonthly: "$4.99", priceYearly: "$3.99", featuresLabel: "INCLUDES", features: ["Education ROI scenarios", "Saved comparisons", "Personal career roadmap"] },
  { id: "business", name: "Plus", description: "For deeper comparisons across more options", priceMonthly: "$9.99", priceYearly: "$7.99", badge: "RECOMMENDED", featuresLabel: "EVERYTHING IN PRO, PLUS", features: ["Advanced scenario comparison", "Scholarship matching", "Skills-gap insights", "Extended roadmap planning"] },
  { id: "enterprise", name: "Teams", description: "For schools, advisors, and education teams", priceMonthly: "$39.99", priceYearly: "$31.99", featuresLabel: "EVERYTHING IN PLUS, PLUS", features: ["Shared scenario library", "Team workspaces", "Advisor-ready summaries"] },
];

export const PRICING_FAQ: ReadonlyArray<readonly [string, string]> = [
  ["How does payment work?", "Payment happens on Stripe's hosted checkout. Fence never sees your card details, and your plan activates as soon as Stripe confirms the payment."],
  ["What is the difference between monthly and yearly billing?", "Yearly billing costs about 20% less per month and is charged once a year. Monthly billing is charged every month."],
  ["Where do the salary and tuition numbers come from?", "From stored market snapshots and official sources, each labelled with where it came from. When Fence has no verified figure, it asks for yours instead of guessing."],
  ["Is a Fence result financial advice?", "No. It is a planning estimate built from data and assumptions you can see. It is not a promise of a salary or a job."],
  ["Can a school or advisor use Fence?", "Yes. The Teams plan is built for schools, advisors and education teams. Write to us from the contact page to set it up."],
];
