/** Decorative composition for the dark auth panel: outlined cards, a payback ring and a dot grid. */
export default function AuthBrandArt() {
  return (
    <div className="auth-brand-art" aria-hidden="true">
      <span className="aba-grid" />
      <span className="aba-ring"><b>4.2<small>years</small></b></span>
      <span className="aba-card aba-card--lime"><small>10-year ROI</small><b>+157%</b><i className="aba-bars"><i /><i /><i /><i /><i /></i></span>
      <span className="aba-card aba-card--violet"><small>Payback</small><b>51 mo</b></span>
      <span className="aba-card aba-card--paper"><small>Start salary</small><b>112k</b><i className="aba-line" /></span>
      <span className="aba-swoosh" />
      <span className="aba-dot aba-dot--1" /><span className="aba-dot aba-dot--2" /><span className="aba-dot aba-dot--3" />
    </div>
  );
}
