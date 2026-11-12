import type { Metadata } from "next";
import { notFound } from "next/navigation";
import SitePage from "../../components/SitePage";

const documents = {
  privacy: { title: "Privacy", copy: "This draft privacy page is a placeholder for Fence’s approved privacy policy. Replace this content with reviewed legal copy before launch." },
  terms: { title: "Terms", copy: "This draft terms page is a placeholder for Fence’s approved terms of service. Replace this content with reviewed legal copy before launch." },
  cookies: { title: "Cookies", copy: "This draft cookie page is a placeholder for Fence’s approved cookie policy. Replace this content with reviewed legal copy before launch." },
} as const;

export function generateStaticParams() {
  return Object.keys(documents).map((document) => ({ document }));
}

export function generateMetadata({ params }: { params: { document: string } }): Metadata {
  const document = documents[params.document as keyof typeof documents];
  // Drafts stay out of search results until reviewed legal copy replaces them.
  return { title: document?.title ?? "Legal", robots: { index: false, follow: true }, alternates: { canonical: `/legal/${params.document}` } };
}

export default function LegalDocumentPage({ params }: { params: { document: string } }) {
  const document = documents[params.document as keyof typeof documents];
  if (!document) notFound();

  return <SitePage kicker="Fence / legal · draft" title={document.title} lead={document.copy}>{null}</SitePage>;
}
