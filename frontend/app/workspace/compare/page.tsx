import type { Metadata } from "next";
import Link from "next/link";
import { Icon, Topography, WorkspacePageHeader } from "../WorkspaceUI";

export const metadata: Metadata = { title: "Compare universities" };

const universities = [
  { name: "WSiiZ", full: "Wyższa Szkoła Informatyki i Zarządzania", city: "Rzeszów", fee: "€6,000", featured: true, mark: "W" },
  { name: "University of Warsaw", full: "Computer Science programmes", city: "Warsaw", fee: "€4,500", mark: "UW" },
  { name: "AGH University of Krakow", full: "Technology and engineering", city: "Kraków", fee: "€4,000", mark: "AGH" },
  { name: "Wrocław University of Science and Technology", full: "Computer Science programmes", city: "Wrocław", fee: "€4,200", mark: "PWr" },
];

export default function CompareUniversitiesPage() {
  return (
    <main className="sketch-page">
      <WorkspacePageHeader
        section="Compare Universities"
        title="Compare your education options"
        highlight="education options"
        description="Explore universities, compare key details and find the best fit for your goals."
      >
        <div className="sketch-card compare-toolbar">
          <label className="sketch-field"><Icon name="globe" /><div><small>Country</small><select defaultValue="Poland" aria-label="Country"><option>Poland</option></select></div></label>
          <label className="sketch-field"><Icon name="graduation" /><div><small>Faculty</small><select defaultValue="Computer Science" aria-label="Faculty"><option>Computer Science</option></select></div></label>
          <label className="sketch-field"><Icon name="search" /><input aria-label="Search university" placeholder="Search university..." /></label>
          <button type="button" className="sketch-btn sketch-btn-violet">Open external directory <Icon name="arrow" size={17} /></button>
        </div>
      </WorkspacePageHeader>

      <p className="compare-found">4 universities found</p>
      <div className="compare-layout">
        <section className="university-grid" aria-label="University results">
          {universities.map((university) => (
            <article className={`sketch-card university-card ${university.featured ? "is-featured" : ""}`} key={university.name}>
              {university.featured && <Topography />}
              <div className="university-brand">
                <span className="university-mark">{university.mark}</span>
                <div><h2>{university.name}</h2><div className="location"><Icon name="pin" size={15} /> {university.city}, Poland</div></div>
              </div>
              <p>{university.full}. Practice-oriented programmes with a strong focus on modern technology and career opportunities.</p>
              <div className="university-facts">
                <div><strong>{university.fee}</strong><small>Annual tuition</small></div>
                <div><strong>3 years</strong><small>Duration (Bachelor&apos;s)</small></div>
                <div><strong>Full-time</strong><small>Study mode</small></div>
              </div>
            </article>
          ))}
        </section>

        <aside className="sketch-card compare-detail">
          <div className="compare-detail-head">
            <Topography />
            <div className="university-brand"><span className="university-mark">W</span><div><h2>WSiiZ</h2><p>Wyższa Szkoła Informatyki<br />i Zarządzania</p></div></div>
          </div>
          <div className="compare-detail-body">
            <div className="compare-tabs"><span className="is-active">Prediction</span><span>About</span></div>
            <h3 className="prediction-title">Education investment <span className="sketch-muted">(illustrative)</span></h3>
            <div className="prediction-metrics">
              <div><strong>€6,000</strong><span>Annual tuition</span></div>
              <div><strong>3 years</strong><span>Duration</span></div>
              <div><strong>€18,000</strong><span>Total</span></div>
            </div>
            <div className="target-role"><Icon name="user" size={31} /><div><strong>Target role · Not set</strong><p>Set your career goal in Roadmap to see relevant insights.</p></div></div>
            <div className="compare-actions">
              <Link href="/workspace/scenario/new" className="sketch-btn" style={{ background: "#151819", color: "#fff" }}>Open full prediction <Icon name="arrow" size={18} /></Link>
              <Link href="/workspace/roadmap" className="sketch-btn sketch-btn-primary">Create roadmap <Icon name="arrow" size={18} /></Link>
            </div>
            <div className="compare-note"><Icon name="info" size={18} /><span><strong>Illustrative scenarios — not verified offers.</strong><br />Information is for comparison purposes only and may change.</span></div>
          </div>
        </aside>
      </div>
    </main>
  );
}

