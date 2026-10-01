"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import "../../../styles/dashboard.css";

export default function UniversityDetailsPage() {
  const params = useParams();
  const scenarioId = params.id as string;
  const [data, setData] = useState<any>(null);
  const [projection, setProjection] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/simulations/${scenarioId}`, { headers: { Accept: "application/json" } });
        if (res.ok) {
          const scenarioData = await res.json();
          setData(scenarioData);
          
          if (scenarioData.current_revision_number) {
            const projRes = await fetch(`/api/simulations/${scenarioId}/revisions/${scenarioData.current_revision_number}/projections`, { headers: { Accept: "application/json" } });
            if (projRes.ok) {
              const projData = await projRes.json();
              if (projData && projData.length > 0) {
                setProjection(projData[0]);
              }
            }
          }
        }
      } catch {
        // silent error for now
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [scenarioId]);

  if (loading) return <div className="dashboard-layout" style={{ paddingTop: 100 }}>Loading details...</div>;

  const title = data?.name || "Computer Science";
  const assumptions = data?.revisions?.at(-1)?.assumptions;
  const university = assumptions?.university || (data?.country === "Poland" ? "WSiiZ" : (data?.country || "University"));
  const location = assumptions?.country || data?.country || "Poland";
  
  // Real calculations if available, else placeholders
  const years = projection?.horizon_years ? Math.min(3, projection.horizon_years) : 3;
  const totalTuition = projection?.total_investment || (6000 * years);
  const tuitionPerYear = totalTuition / years;
  const estSalary = projection?.estimated_start_salary || 24000;
  const currency = projection?.currency || data?.currency || "USD";
  const paybackText = projection?.payback_months ? `${Math.round(projection.payback_months/12 * 10)/10} years` : "3 years";
  
  const fmtCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency, maximumFractionDigits: 0 }).format(val);
  };

  return (
    <div className="dashboard-layout" style={{ paddingTop: "40px" }}>
      
      <div className="univ-details-header">
        <p className="dashboard-breadcrumb">Saved scenarios <i>/</i> {university} <i>/</i> Full details</p>
        <Link href="/workspace/scenarios" className="univ-back-link">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          Back to scenarios
        </Link>

        <div className="univ-header-top">
          <div className="univ-header-title">
            <h1>{university} • {title}</h1>
            <div className="univ-header-meta">
              <div className="univ-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                {location}
              </div>
              <div className="univ-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                On-campus
              </div>
              <div className="univ-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
                Bachelor's degree
              </div>
              <div className="univ-meta-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                {years} years
              </div>
            </div>
          </div>
          <div className="univ-header-actions">
            <button type="button" className="btn-official-site" disabled aria-disabled="true">
              Official university website
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
            </button>
            <div className="univ-sample-notice">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              Sample content — verify with university
            </div>
          </div>
        </div>
      </div>

      <div className="univ-tabs">
        <div className="univ-tab is-active">Overview</div>
        <div className="univ-tab">Admissions</div>
        <div className="univ-tab">Subjects</div>
        <div className="univ-tab">Scholarships</div>
        <div className="univ-tab">Forecast</div>
      </div>

      <div className="univ-grid">
        
        {/* Card 1: Admissions */}
        <div className="ud-card">
          <div className="ud-card-header">
            <div className="ud-card-title">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              Admissions & documents
            </div>
            <p className="ud-card-subtitle">Example checklist</p>
          </div>
          <div className="ud-list">
            <div className="ud-list-item">
              <div className="ud-list-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg></div>
              <div className="ud-list-text">
                <strong>School-leaving certificate</strong>
                <p>e.g. high school diploma or equivalent</p>
              </div>
            </div>
            <div className="ud-list-item">
              <div className="ud-list-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
              <div className="ud-list-text">
                <strong>Identity document</strong>
                <p>e.g. passport or national ID</p>
              </div>
            </div>
            <div className="ud-list-item">
              <div className="ud-list-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
              <div className="ud-list-text">
                <strong>Language proficiency evidence</strong>
                <p>e.g. English language certificate (if required)</p>
              </div>
            </div>
          </div>
          <div className="ud-card-footer">
            <p className="ud-card-notice">Requirements depend on the programme and applicant.</p>
            <div className="ud-btn-row">
              <button type="button" className="ud-btn-pill" disabled>Official admissions page ↗</button>
              <button type="button" className="ud-btn-pill" disabled>Document requirements ↗</button>
            </div>
          </div>
        </div>

        {/* Card 2: Subjects */}
        <div className="ud-card is-dark">
          <div className="ud-card-header">
            <div className="ud-card-title">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
              Programme subjects
            </div>
            <p className="ud-card-subtitle">Example curriculum</p>
          </div>
          <div className="ud-list">
            <div className="ud-nav-item"><span>Programming fundamentals</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg></div>
            <div className="ud-nav-item"><span>Mathematics</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg></div>
            <div className="ud-nav-item"><span>Databases</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg></div>
            <div className="ud-nav-item"><span>Software engineering</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg></div>
          </div>
          <div className="ud-card-footer">
            <p className="ud-card-notice">This is an example of subject areas. Actual curriculum may differ — please verify with the university.</p>
            <button type="button" className="ud-btn-full is-lime" disabled>Official programme curriculum ↗</button>
          </div>
        </div>

        {/* Card 3: Scholarships */}
        <div className="ud-card">
          <div className="ud-card-header">
            <div className="ud-card-title">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
              Scholarships
            </div>
            <p className="ud-card-subtitle">Example categories</p>
          </div>
          <div className="ud-list">
            <div className="ud-nav-item">
              <div className="ud-list-text">
                <strong>Need-based support</strong>
                <p>e.g. for students with financial need</p>
              </div>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
            </div>
            <div className="ud-nav-item">
              <div className="ud-list-text">
                <strong>Academic achievement</strong>
                <p>e.g. merit-based scholarships</p>
              </div>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
            </div>
            <div className="ud-nav-item">
              <div className="ud-list-text">
                <strong>External funding</strong>
                <p>e.g. government or private organisations</p>
              </div>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
            </div>
          </div>
          <div className="ud-card-footer">
            <p className="ud-card-notice">Eligibility, deadlines and availability require verification.</p>
            <button type="button" className="ud-btn-full is-violet-solid" disabled>View official scholarship information ↗</button>
          </div>
        </div>

        {/* Card 4: Motivation Letter */}
        <div className="ud-card">
          <div className="ud-card-header">
            <div className="ud-card-title">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              Motivation letter assistant
            </div>
            <p className="ud-card-subtitle">Draft from your real background and reasons for applying.</p>
          </div>
          <div className="ud-list" style={{ marginTop: "16px" }}>
            <button className="ud-btn-full is-violet-solid" style={{ marginBottom: "12px" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              Start a draft
            </button>
            <button className="ud-btn-full is-white">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              Upload existing letter
            </button>
          </div>
          <div className="ud-card-footer">
            <p className="ud-card-notice">Review and edit the letter before use. Make sure it reflects your own experience and meets the university's requirements.</p>
          </div>
        </div>

        {/* Card 5: Forecast */}
        <div className="ud-card is-dark">
          <div className="ud-card-header">
            <div className="ud-card-title">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18 9l-5 5-3-3-5 5"/></svg>
              Preliminary forecast
            </div>
          </div>
          <div className="ud-list">
            <div className="ud-forecast-row">
              <div className="ud-forecast-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M12 12h.01"/><path d="M17 12h.01"/><path d="M7 12h.01"/></svg>
                <span>Tuition fees {projection ? "" : "(example)"}</span>
              </div>
              <div className="ud-forecast-val">
                <strong>{fmtCurrency(tuitionPerYear)} / year</strong>
                <p>× {years} years = {fmtCurrency(totalTuition)}</p>
              </div>
            </div>
            <div className="ud-forecast-row">
              <div className="ud-forecast-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18 9l-5 5-3-3-5 5"/></svg>
                <span>Estimated salary {projection ? "" : "(example)"}</span>
              </div>
              <div className="ud-forecast-val">
                <strong>{fmtCurrency(estSalary)} / year</strong>
                <p>(after graduation)</p>
              </div>
            </div>
            <div className="ud-forecast-row">
              <div className="ud-forecast-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                <span>Payback period {projection ? "" : "(example)"}</span>
              </div>
              <div className="ud-forecast-val">
                <strong>{paybackText}</strong>
                <p>at {fmtCurrency(tuitionPerYear)} annual repayment budget</p>
              </div>
            </div>
          </div>
          <div className="ud-card-footer">
            <p className="ud-card-notice">Excludes taxes, living expenses and other costs. For illustrative purposes only — actual costs and outcomes may vary.</p>
            <Link href="/workspace/overview" className="ud-btn-full is-lime">
              Open full calculation →
            </Link>
          </div>
        </div>

        {/* Card 6: Career Roadmap */}
        <div className="ud-card">
          <div className="ud-card-header">
            <div className="ud-card-title">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
              Career roadmap
            </div>
            <p className="ud-card-subtitle">What career goal would you like to work towards?</p>
          </div>
          <div className="ud-list" style={{ marginTop: "16px" }}>
            <div className="ud-input-group">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" className="ud-input" placeholder="Choose or enter a career goal..." />
            </div>
          </div>
          <div className="ud-card-footer">
            <p className="ud-card-notice">Optional — no goal selected yet.</p>
            <button className="ud-btn-full is-lime">Create roadmap</button>
          </div>
        </div>

      </div>
    </div>
  );
}
