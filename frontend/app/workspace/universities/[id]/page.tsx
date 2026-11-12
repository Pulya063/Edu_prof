"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { WorkspacePageHeader } from "../../WorkspaceUI";
import { WorkspaceUniversityDetails, workspaceFetch } from "@/lib/api/workspace";
import UniversityDetails from "../UniversityDetails";

export default function UniversityDetailsPage() {
  const params = useParams<{ id: string }>();
  const [university, setUniversity] = useState<WorkspaceUniversityDetails | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    workspaceFetch<WorkspaceUniversityDetails>(`/api/workspace/universities/${encodeURIComponent(params.id)}`)
      .then(setUniversity)
      .catch((reason) => setError(reason.message));
  }, [params.id]);

  if (!university) return <main className="sketch-page"><WorkspacePageHeader section="Compare / University details" title="University details" highlight="details" description="Programme, cost and application information in one place." />{error ? <div className="workspace-status is-error">{error}</div> : <div className="workspace-status">Loading university details…</div>}</main>;

  return <main className="sketch-page university-full-page">
    <WorkspacePageHeader section="Compare / University details" title={university.name} highlight={university.name} description={[university.profile?.facts.city || university.city, university.country].filter(Boolean).join(", ")} />
    <Link href="/workspace/compare" className="university-back">← Back to comparison</Link>
    <UniversityDetails university={university} />
  </main>;
}
