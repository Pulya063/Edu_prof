import type { Metadata } from "next";
import "./globals.css";
import "./footer.css";
import "./final-pass.css";

export const metadata: Metadata = {
  title: "Fence — demo",
  description: "Understand the cost and potential return of your education.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
