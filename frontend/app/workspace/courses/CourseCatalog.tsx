"use client";

import { useRef, useState } from "react";
import { Icon, WorkspacePageHeader } from "../WorkspaceUI";

const courses = [
  { id: "sql", title: "SQL fundamentals", description: "Learn the core concepts of SQL and practice with real-world data examples.", icon: "database" as const, duration: "4–6 hours" },
  { id: "fastapi", title: "FastAPI from zero", description: "Build practical APIs with validation, documentation and testing.", icon: "code" as const, duration: "6–8 hours" },
  { id: "git", title: "Git essentials", description: "Master version control with Git and collaborate confidently on real projects.", icon: "spark" as const, duration: "3–5 hours" },
  { id: "testing", title: "Python testing", description: "Write reliable automated tests and improve the quality of your projects.", icon: "tasks" as const, duration: "5–7 hours" },
];

export default function CourseCatalog() {
  const [selectedId, setSelectedId] = useState("sql");
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const selected = courses.find((course) => course.id === selectedId);
  const filtered = courses.filter((course) => course.title.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="course-shell">
      <main className={`sketch-page course-page ${selected ? "has-drawer" : ""}`}>
        <WorkspacePageHeader section="Course search" title="Find courses that fit your plan" highlight="courses" description="Build in-demand skills with curated learning resources." />
        <section className="sketch-card course-filters">
          <div className="course-search"><Icon name="search"/><input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by topic or skill (e.g. SQL, FastAPI, data analysis)" aria-label="Search courses"/>{query && <button type="button" onClick={() => { setQuery(""); inputRef.current?.focus(); }} aria-label="Clear search">×</button>}</div>
          <div className="course-filter-grid"><label className="sketch-field"><div><small>Level</small><select aria-label="Level" defaultValue="All levels"><option>All levels</option></select></div></label><label className="sketch-field"><div><small>Language</small><select aria-label="Language" defaultValue="All languages"><option>All languages</option></select></div></label><label className="sketch-field"><div><small>Free / Paid</small><select aria-label="Price" defaultValue="Any"><option>Any</option></select></div></label><label className="sketch-field"><div><small>Format</small><select aria-label="Format" defaultValue="Any"><option>Any</option></select></div></label></div>
          <div className="course-suggestions"><span>Suggested from your roadmap · SQL &amp; APIs</span><span className="sketch-chip is-active">SQL</span><span className="sketch-chip is-active">FastAPI</span><span className="sketch-chip is-active">API design</span><span className="sketch-chip is-active">Testing</span></div>
        </section>
        <h2 style={{ margin: "22px 6px 12px" }}>{filtered.length} courses found</h2>
        <section className="course-grid" aria-label="Courses">
          {filtered.map((course) => <article className={`sketch-card course-card ${selectedId === course.id ? "is-selected" : ""}`} key={course.id}><div className="course-art"><Icon name={course.icon} size={60}/></div><div className="course-content"><span className="sketch-chip">Course</span><h3>{course.title}</h3><p>{course.description}</p><div className="course-meta"><span className="sketch-chip">Beginner</span><span className="sketch-chip">English</span><span className="sketch-chip">Self-paced</span><span className="sketch-chip">{course.duration}</span></div><div className="course-footer"><button type="button" className="course-link" onClick={() => setSelectedId(course.id)}>Open course ↗</button><button type="button" className="sketch-btn" aria-label={`Save ${course.title}`}>Save</button></div></div></article>)}
        </section>
      </main>
      {selected && <aside className="course-drawer" aria-label="Course details"><button type="button" className="course-drawer-close" onClick={() => setSelectedId("")} aria-label="Close course details">×</button><small>Course details</small><div className="course-drawer-hero"><span className="course-art" style={{ width: 150, height: 100 }}><Icon name={selected.icon} size={55}/></span><div><h2>{selected.title}</h2><span className="sketch-chip is-active">Demo course</span></div></div><h3>Build a practical foundation</h3><p>Learn through concise explanations and hands-on exercises designed around real project work.</p><div className="course-detail-grid"><div><span>Level</span><strong>Beginner</strong></div><div><span>Language</span><strong>English</strong></div><div><span>Format</span><strong>Self-paced</strong></div><div><span>Duration</span><strong>{selected.duration}</strong></div></div><h3>What you will learn</h3><ul className="learn-list"><li>Use the core concepts in a practical project</li><li>Connect tools and data confidently</li><li>Practice with guided exercises</li></ul><h3>Course programme</h3><ol className="programme-list"><li><span>01</span>Core concepts and foundations</li><li><span>02</span>Guided practical workflow</li><li><span>03</span>Practice exercises</li></ol><h3>Before you start</h3><p>No prior specialist knowledge required.</p><h3>Provider &amp; enrolment</h3><p>Sample listing · provider not connected. Price and availability: check provider.</p><div className="course-drawer-actions"><button type="button" className="sketch-btn sketch-btn-primary">Enrol on provider website <Icon name="arrow" size={17}/></button><button type="button" className="sketch-btn">Save course</button></div></aside>}
    </div>
  );
}

