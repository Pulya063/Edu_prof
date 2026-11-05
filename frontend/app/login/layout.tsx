import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Log in",
  description: "Sign in to your Fence workspace to see your saved education scenarios, payback and career roadmap.",
  robots: { index: false, follow: true },
  alternates: { canonical: "/login" },
};

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
