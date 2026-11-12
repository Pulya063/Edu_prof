import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create an account",
  description: "Create a Fence account to calculate when your degree pays back and compare universities.",
  robots: { index: false, follow: true },
  alternates: { canonical: "/register" },
};

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
