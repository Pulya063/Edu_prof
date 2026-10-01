"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import "../../styles/dashboard.css";

type UserProfile = {
  id: number;
  email: string;
  username: string;
  created_at: string;
  plan: string;
  plan_limits: { roi_calculations: number | null; roadmaps: number | null };
  plan_features: string[];
  usage: { roi_calculations: number; roadmaps: number };
  calculations_remaining: number;
};

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProfile() {
      try {
        const res = await fetch("/api/auth/me", { headers: { Accept: "application/json" } });
        if (!res.ok) {
          if (res.status === 401) router.push("/login");
          return;
        }
        setProfile(await res.json());
      } catch {
        // Handle error silently for now
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, [router]);

  if (loading) return <div className="dashboard-layout" style={{ paddingTop: 100 }}>Loading profile...</div>;
  if (!profile) return null;

  // Derive display names
  const displayName = profile.username && profile.username !== "user" ? profile.username : "Andrii Avramenko"; // fallback for visual match
  const initials = displayName.split(" ").map(n => n[0]).join("").toUpperCase().substring(0, 2);
  const usedScenarios = profile.usage.roi_calculations;
  const limitScenarios = profile.plan_limits.roi_calculations || 3;
  const remainingScenarios = Math.max(0, limitScenarios - usedScenarios);

  return (
    <div className="dashboard-layout">
      <header className="dashboard-header">
        <p className="dashboard-breadcrumb">Workspace <i>/</i> Profile</p>
        <div className="dashboard-title-row">
          <h1>Your profile</h1>
          <span className="demo-pill">DEMO DATA</span>
        </div>
        <p>Manage your information, track your progress, and tailor your experience.</p>
      </header>

      <div className="profile-grid">
        
        {/* Widget 1: Profile information */}
        <div className="widget widget-profile-info">
          <div className="pi-header">
            <div className="pi-user">
              <div className="pi-avatar">{initials}</div>
              <div className="pi-user-info">
                <h2>{displayName}</h2>
                <p>{profile.email}</p>
              </div>
            </div>
            <button className="btn-edit-profile">Edit profile</button>
          </div>
          
          <div className="pi-divider"></div>
          
          <div className="pi-form-row">
            <div className="pi-input-group">
              <label>Field of study</label>
              <select className="pi-select" defaultValue="Computer Science">
                <option value="Computer Science">Computer Science</option>
                <option value="Data Science">Data Science</option>
              </select>
            </div>
            <div className="pi-input-group">
              <label>Country</label>
              <select className="pi-select" defaultValue="Poland">
                <option value="Poland">Poland</option>
                <option value="Ukraine">Ukraine</option>
                <option value="UK">United Kingdom</option>
              </select>
            </div>
          </div>
          
          <div className="pi-input-group">
            <label>About me</label>
            <textarea className="pi-textarea" placeholder="Tell us a bit about yourself (optional)"></textarea>
            <span className="pi-char-count">0/300</span>
          </div>
        </div>

        <div>
          {/* Widget 2: Your plan */}
          <div className="widget widget-plan" style={{ marginBottom: "24px" }}>
            <div className="plan-header">
              <h3>Your plan</h3>
              <span className="plan-pill">Free plan</span>
            </div>
            <p className="plan-desc">Explore Fence with up to {limitScenarios} scenario slots.</p>
            
            <div className="plan-stats">
              <div className="plan-stat">
                <strong>{usedScenarios} / {limitScenarios}</strong>
                <span>Scenarios used</span>
              </div>
              <div className="plan-stat-divider"></div>
              <div className="plan-stat">
                <strong>{remainingScenarios}</strong>
                <span>Scenario slot remaining</span>
              </div>
            </div>
            
            <button className="btn-plan-options">
              View plan options
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
            </button>
          </div>

          {/* Widget 3: Your current skills */}
          <div className="widget widget-skills">
            <h3>Your current skills</h3>
            <p>Add skills to get more relevant insights and recommendations.</p>
            
            <div className="skills-tags">
              <span className="skill-tag">Python basics</span>
              <span className="skill-tag">Git</span>
            </div>
            
            <div className="career-target-label">Career target</div>
            <span className="career-target-tag">Not set</span>
            <div className="career-target-hint">Add a career target after using the Roadmap.</div>
          </div>
        </div>

        {/* Widget 4: Resume assistant */}
        <div className="widget widget-resume">
          <div className="resume-header">
            <h3>Resume assistant</h3>
            <p>Turn your real education, skills and projects into a clear CV.</p>
          </div>
          
          <div className="resume-steps">
            <div className="resume-step">
              <svg className="resume-step-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              <span className="resume-step-pill">1. Add your experience</span>
            </div>
            <div className="resume-step-line"></div>
            
            <div className="resume-step">
              <svg className="resume-step-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              <span className="resume-step-pill">2. Improve your wording</span>
            </div>
            <div className="resume-step-line"></div>
            
            <div className="resume-step">
              <svg className="resume-step-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <span className="resume-step-pill">3. Review your CV</span>
            </div>
          </div>
          
          <div className="resume-footer">
            <p>Start from your profile or upload an existing resume. Review every detail before using it.</p>
            <div className="resume-actions">
              <button className="btn-upload">Upload resume</button>
              <button className="btn-create">
                Create my resume
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></svg>
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
