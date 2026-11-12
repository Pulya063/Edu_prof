import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Reset password",
  description: "Reset the password for your Fence account.",
  robots: { index: false, follow: true },
  alternates: { canonical: "/reset-password" },
};

export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
