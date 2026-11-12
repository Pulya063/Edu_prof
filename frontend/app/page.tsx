import type { Metadata } from "next";
import HomeClient from "./HomeClient";
import JsonLd from "./components/JsonLd";
import { SITE_URL } from "./utils/site";

export const metadata: Metadata = {
  title: { absolute: "Fence — Education ROI Calculator for Poland & Ukraine" },
  description: "See what a degree really costs, when it pays back and the 10-year ROI, from live salary data for Poland and Ukraine. Compare universities and plan your career.",
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return (
    <>
      <JsonLd data={[
        {
          "@context": "https://schema.org",
          "@type": "Organization",
          name: "Fence",
          url: SITE_URL,
          logo: `${SITE_URL}/icon.svg`,
          description: "Education ROI and career decision planning for students, parents and career changers.",
        },
        {
          "@context": "https://schema.org",
          "@type": "WebSite",
          name: "Fence",
          url: SITE_URL,
          inLanguage: ["en", "uk", "pl"],
        },
      ]} />
      <HomeClient />
    </>
  );
}
