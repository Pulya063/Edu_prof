import { notFound } from "next/navigation";

const documents = {
  privacy: { title: "Privacy", copy: "This draft privacy page is a placeholder for Fence’s approved privacy policy. Replace this content with reviewed legal copy before launch." },
  terms: { title: "Terms", copy: "This draft terms page is a placeholder for Fence’s approved terms of service. Replace this content with reviewed legal copy before launch." },
  cookies: { title: "Cookies", copy: "This draft cookie page is a placeholder for Fence’s approved cookie policy. Replace this content with reviewed legal copy before launch." },
} as const;

export function generateStaticParams() {
  return Object.keys(documents).map((document) => ({ document }));
}

export default function LegalDocumentPage({ params }: { params: { document: string } }) {
  const document = documents[params.document as keyof typeof documents];
  if (!document) notFound();

  return <main className="legal-page"><a href="/">← Back to Fence</a><p className="legal-kicker">Fence / legal</p><h1>{document.title}</h1><p>{document.copy}</p></main>;
}
