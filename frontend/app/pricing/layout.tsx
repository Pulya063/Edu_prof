import type { Metadata } from "next";
import JsonLd from "../components/JsonLd";
import { PLANS, PRICING_FAQ } from "./plans";

export const metadata: Metadata = {
  title: "Pricing — Education ROI Plans from $3.99 a Month",
  description: "Fence plans from $3.99 a month: education ROI scenarios, university comparison and a career roadmap. Billed securely through Stripe.",
  alternates: { canonical: "/pricing" },
};

export default function PricingLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <JsonLd data={[
        {
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "Fence",
          applicationCategory: "EducationalApplication",
          operatingSystem: "Web",
          offers: PLANS.map((plan) => ({
            "@type": "Offer",
            name: plan.name,
            price: plan.priceMonthly.replace("$", ""),
            priceCurrency: "USD",
            description: plan.description,
          })),
        },
        {
          "@context": "https://schema.org",
          "@type": "FAQPage",
          mainEntity: PRICING_FAQ.map(([question, answer]) => ({
            "@type": "Question",
            name: question,
            acceptedAnswer: { "@type": "Answer", text: answer },
          })),
        },
      ]} />
      {children}
    </>
  );
}
