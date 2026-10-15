"use client";

import { useEffect, useRef, useState } from "react";
import { Icon, WorkspacePageHeader } from "../WorkspaceUI";
import { WorkspaceCourse, workspaceFetch } from "@/lib/api/workspace";

export default function CourseCatalog() {
  const [courses, setCourses] = useState<WorkspaceCourse[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState("All levels");
  const [language, setLanguage] = useState("All languages");
  const [format, setFormat] = useState("Any");
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true); setError("");
      const params = new URLSearchParams({ q: query, level, language, format });
      workspaceFetch<WorkspaceCourse[]>(`/api/workspace/courses?${params}`, { signal: controller.signal }).then((items) => { setCourses(items); setSelectedId((current) => items.some((item) => item.id === current) ? current : ""); }).catch((reason) => { if (reason.name !== "AbortError") setError(reason.message); }).finally(() => setLoading(false));
    }, 250);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [query, level, language, format]);

  useEffect(() => {
    if (!selectedId) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" || event.key === "Esc") {
        event.preventDefault();
        setSelectedId("");
      }
    };
    document.addEventListener("keydown", closeOnEscape, true);
    return () => document.removeEventListener("keydown", closeOnEscape, true);
  }, [selectedId]);
  const selected = courses.find((course) => course.id === selectedId);

  async function toggleSave(course: WorkspaceCourse) {
    setBusyId(course.id); setError("");
    try { const next = await workspaceFetch<WorkspaceCourse>(`/api/workspace/courses/${course.id}/save`, { method: course.saved ? "DELETE" : "POST" }); setCourses((items) => items.map((item) => item.id === next.id ? next : item)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save the course."); }
    finally { setBusyId(""); }
  }

  return <div className="course-shell"><main className={`sketch-page course-page ${selected ? "has-drawer" : ""}`}><WorkspacePageHeader section="Course search" title="Find courses that fit your plan" highlight="courses" description="Build in-demand skills with curated learning resources." />
    {error && <div className="workspace-status is-error">{error}</div>}
    <section className="sketch-card course-filters"><div className="course-search"><Icon name="search"/><input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by topic or skill (e.g. SQL, FastAPI, data analysis)" aria-label="Search courses"/>{query && <button type="button" onClick={() => { setQuery(""); inputRef.current?.focus(); }} aria-label="Clear search">×</button>}</div><div className="course-filter-grid"><label className="sketch-field"><div><small>Level</small><select value={level} onChange={(event) => setLevel(event.target.value)}><option>All levels</option><option>Beginner</option><option>Intermediate</option></select></div></label><label className="sketch-field"><div><small>Language</small><select value={language} onChange={(event) => setLanguage(event.target.value)}><option>All languages</option><option>English</option></select></div></label><label className="sketch-field"><div><small>Free / Paid</small><select value="Any" disabled><option>Any</option></select></div></label><label className="sketch-field"><div><small>Format</small><select value={format} onChange={(event) => setFormat(event.target.value)}><option>Any</option><option>Self-paced</option></select></div></label></div><div className="course-suggestions"><span>Suggested skills</span>{["SQL", "FastAPI", "Git", "Testing"].map((skill) => <button type="button" className="sketch-chip is-active" key={skill} onClick={() => setQuery(skill)}>{skill}</button>)}</div></section>
    <h2 style={{ margin: "22px 6px 12px" }}>{loading ? "Loading courses…" : `${courses.length} courses found`}</h2><section className="course-grid" aria-label="Courses">{courses.map((course) => <article className={`sketch-card course-card ${selectedId === course.id ? "is-selected" : ""}`} key={course.id} role="button" tabIndex={0} aria-label={`Open ${course.title} details`} onClick={() => setSelectedId(course.id)} onKeyDown={(event) => { if (event.currentTarget !== event.target) return; if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setSelectedId(course.id); } }}><div className="course-art"><Icon name={course.skills.includes("SQL") ? "database" : course.skills.includes("FastAPI") ? "code" : "spark"} size={60}/></div><div className="course-content"><span className="sketch-chip">Course</span><h3>{course.title}</h3><p>{course.description}</p><div className="course-meta"><span className="sketch-chip">{course.level}</span><span className="sketch-chip">{course.language}</span><span className="sketch-chip">{course.format}</span><span className="sketch-chip">{course.duration}</span></div><div className="course-footer"><button type="button" className="course-link" onClick={() => setSelectedId(course.id)}>Open course ↗</button><button type="button" disabled={busyId === course.id} className="sketch-btn" onClick={(event) => { event.stopPropagation(); void toggleSave(course); }}>{busyId === course.id ? "Saving…" : course.saved ? "Saved ✓" : "Save"}</button></div></div></article>)}{!loading && !courses.length && <div className="workspace-status">No courses match these filters.</div>}</section></main>
    {selected && <aside className="course-drawer" aria-label="Course details"><button type="button" className="course-drawer-close" onClick={() => setSelectedId("")} aria-label="Close course details">×</button><small>Course details</small><div className="course-drawer-hero"><span className="course-art" style={{ width: 150, height: 100 }}><Icon name={selected.skills.includes("SQL") ? "database" : "code"} size={55}/></span><div><h2>{selected.title}</h2><span className="sketch-chip is-active">Fence catalog</span></div></div><h3>{selected.description}</h3><div className="course-detail-grid"><div><span>Level</span><strong>{selected.level}</strong></div><div><span>Language</span><strong>{selected.language}</strong></div><div><span>Format</span><strong>{selected.format}</strong></div><div><span>Duration</span><strong>{selected.duration}</strong></div></div><h3>What you will learn</h3><ul className="learn-list">{selected.skills.map((skill) => <li key={skill}>{skill}</li>)}</ul><h3>Provider &amp; enrolment</h3><p>{selected.provider_name}. {selected.provider_url ? "Official provider link is available." : "Provider enrolment is not connected yet."}</p><div className="course-drawer-actions">{selected.provider_url ? <a href={selected.provider_url} target="_blank" rel="noreferrer" className="sketch-btn sketch-btn-primary">Enrol on provider website <Icon name="arrow" size={17}/></a> : <button type="button" disabled className="sketch-btn sketch-btn-primary">Provider unavailable</button>}<button type="button" disabled={busyId === selected.id} className="sketch-btn" onClick={() => toggleSave(selected)}>{selected.saved ? "Remove from saved" : "Save course"}</button></div></aside>}
  </div>;
}
