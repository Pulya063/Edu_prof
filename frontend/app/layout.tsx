import type { Metadata } from "next";
import "./globals.css";
import "./styles/footer.css";
import "./styles/final-pass.css";
import "./styles/responsive.css";
import { LanguageProvider } from "./context/LanguageContext";
import { SITE_URL } from "./utils/site";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Fence — Education ROI Calculator for Poland & Ukraine",
    template: "%s | Fence",
  },
  description: "Compare education costs, salary assumptions, payback periods, career paths, scholarships, and skills gaps before choosing your next move.",
  keywords: [
    "education ROI calculator",
    "university comparison",
    "career salary forecast",
    "education cost calculator",
    "career roadmap",
    "scholarship matching",
  ],
  applicationName: "Fence",
  category: "education",
  robots: { index: true, follow: true },
  openGraph: {
    type: "website",
    siteName: "Fence",
    title: "Fence — Compare Education Cost, Career Outcomes, and ROI",
    description: "Model education costs and career outcomes in one connected decision view.",
    url: "/",
    locale: "en_US",
    alternateLocale: ["uk_UA", "pl_PL"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Fence — Education ROI and Career Decisions",
    description: "Compare the cost, career outcome, and next steps behind an education path.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        {/* Preconnect to Google Fonts to eliminate DNS + TLS latency */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
