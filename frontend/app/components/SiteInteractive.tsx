"use client";

import { useMemo, useState } from "react";

/* Small interactive pieces for the public sub-pages. Every number here is computed by the
   formulas below from the visitor's own slider values; nothing is fetched or generated. */

const money = (value: number) => Math.round(value).toLocaleString("en-US").replace(/,/g, " ");

/** Hero decoration for sub-pages: three outlined, colour-blocked cards that drift. */
export function SiteHeroArt({ items }: { items: ReadonlyArray<readonly [string, string]> }) {
  return (
    <div className="site-hero-art" aria-hidden="true">
      <span className="sha-ring" />
      <span className="sha-dots" />
      {items.map(([label, value], index) => (
        <span key={label} className={`sha-card sha-card--${index}`}><small>{label}</small><b>{value}</b></span>
      ))}
    </div>
  );
}

const products = [
  {
    key: "calc", tone: "lime", title: "Calculation",
    body: "Cost, the income you give up, payback and ROI for one university and one career target.",
    rows: [["Direct cost", "32 000"], ["Income given up", "230 400"], ["Payback", "64 months"]],
  },
  {
    key: "compare", tone: "violet", title: "University comparison",
    body: "Tuition and outcome data side by side, each figure with its source.",
    bars: [["Programme A", 86], ["Programme B", 48], ["Programme C", 72]],
  },
  {
    key: "roadmap", tone: "ink", title: "Career roadmap",
    body: "Skills, courses and experience between where you are and the role you want. Tick steps off as you go.",
    steps: ["Pick a target role", "Learn Python and SQL", "Ship two portfolio projects", "Apply for an internship"],
  },
] as const;

/** "What Fence does": tabs that swap a colour-blocked panel with a tiny working preview. */
export function ProductTabs() {
  const [active, setActive] = useState(0);
  const [done, setDone] = useState<boolean[]>([true, true, false, false]);
  const product = products[active];
  return (
    <div className="product-tabs">
      <div className="product-tab-list" role="tablist" aria-label="Fence features">
        {products.map((item, index) => (
          <button key={item.key} type="button" role="tab" id={`tab-${item.key}`} aria-controls={`panel-${item.key}`} aria-selected={active === index}
            className={`product-tab product-tab--${item.tone}`} onClick={() => setActive(index)}>
            <span className="product-tab-index">0{index + 1}</span>{item.title}
          </button>
        ))}
      </div>
      <div className={`product-panel product-panel--${product.tone}`} role="tabpanel" id={`panel-${product.key}`} aria-labelledby={`tab-${product.key}`} key={product.key}>
        <div className="product-panel-copy">
          <h3>{product.title}</h3>
          <p>{product.body}</p>
        </div>
        <div className="product-preview">
          {"rows" in product && product.rows.map(([label, value]) => (
            <div className="pp-row" key={label}><span>{label}</span><b>{value}</b></div>
          ))}
          {"bars" in product && product.bars.map(([label, value]) => (
            <div className="pp-bar" key={label}><span>{label}</span><i style={{ width: `${value}%` }} /></div>
          ))}
          {"steps" in product && product.steps.map((step, index) => (
            <label className={`pp-step ${done[index] ? "is-done" : ""}`} key={step}>
              <input type="checkbox" checked={done[index]} onChange={() => setDone((value) => value.map((item, i) => (i === index ? !item : item)))} />
              <span aria-hidden="true">{done[index] ? "✓" : ""}</span>{step}
            </label>
          ))}
          {"steps" in product && <small className="pp-progress">{done.filter(Boolean).length} of {done.length} steps done</small>}
          {"rows" in product && <small className="pp-progress">Example, PLN, today&rsquo;s money</small>}
          {"bars" in product && <small className="pp-progress">Example 10-year return index</small>}
        </div>
      </div>
    </div>
  );
}

function Slider({ label, value, min, max, step, suffix, onChange }: { label: string; value: number; min: number; max: number; step: number; suffix: string; onChange: (value: number) => void }) {
  return (
    <label className="pg-slider">
      <span className="pg-slider-head"><span>{label}</span><b>{money(value)} {suffix}</b></span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))}
        style={{ "--fill": `${((value - min) / (max - min)) * 100}%` } as React.CSSProperties} />
    </label>
  );
}

/** A pocket version of the Fence model: today's money, no salary growth, 100% of work given up. */
export function PaybackPlayground() {
  const [tuition, setTuition] = useState(8000);
  const [years, setYears] = useState(4);
  const [baseline, setBaseline] = useState(4800);
  const [target, setTarget] = useState(9400);
  const [search, setSearch] = useState(3);

  const result = useMemo(() => {
    const direct = tuition * years;
    const opportunity = baseline * 12 * years;
    const investment = direct + opportunity;
    const gain = target - baseline;
    let cumulative = 0;
    let payback: number | null = null;
    const yearly: number[] = [];
    for (let month = 1; month <= 120; month += 1) {
      cumulative += month <= search ? -baseline : gain;
      if (payback === null && cumulative >= investment) payback = month;
      if (month % 12 === 0) yearly.push(cumulative);
    }
    const roi = investment > 0 ? ((cumulative - investment) / investment) * 100 : 0;
    return { direct, opportunity, investment, payback, roi, yearly };
  }, [tuition, years, baseline, target, search]);

  const scale = Math.max(result.investment, ...result.yearly, 1);
  return (
    <div className="playground">
      <div className="pg-controls">
        <Slider label="Tuition per year" value={tuition} min={0} max={40000} step={1000} suffix="PLN" onChange={setTuition} />
        <Slider label="Study years" value={years} min={1} max={6} step={1} suffix="yrs" onChange={setYears} />
        <Slider label="Monthly pay without the degree" value={baseline} min={0} max={12000} step={100} suffix="PLN" onChange={setBaseline} />
        <Slider label="Monthly pay after graduating" value={target} min={1000} max={25000} step={100} suffix="PLN" onChange={setTarget} />
        <Slider label="Months to find the first job" value={search} min={0} max={12} step={1} suffix="mo" onChange={setSearch} />
      </div>
      <div className="pg-result" aria-live="polite">
        <div className="pg-stats">
          <div className="pg-stat pg-stat--paper"><small>Investment</small><b>{money(result.investment)}</b><span>{money(result.direct)} direct + {money(result.opportunity)} given up</span></div>
          <div className="pg-stat pg-stat--lime"><small>Payback after graduating</small><b>{result.payback === null ? "10y+" : `${result.payback} mo`}</b><span>{result.payback === null ? "not within 10 years" : `≈ ${(result.payback / 12).toFixed(1)} years`}</span></div>
          <div className="pg-stat pg-stat--violet"><small>10-year ROI</small><b>{result.roi >= 0 ? "+" : ""}{result.roi.toFixed(0)}%</b><span>gain vs. investment</span></div>
        </div>
        <div className="pg-chart" role="img" aria-label="Cumulative gain for each of the 10 years after graduating, against the investment line">
          <span className="pg-chart-plot"><span className="pg-chart-line" style={{ bottom: `${(result.investment / scale) * 100}%` }}><em>investment</em></span></span>
          {result.yearly.map((value, index) => (
            <span key={index} className={`pg-col ${value >= result.investment ? "is-paid" : ""}`}>
              <i style={{ height: `${Math.max(0, value / scale) * 100}%` }} />
              <small>{index + 1}</small>
            </span>
          ))}
        </div>
        <p className="pg-note">Illustration in today&rsquo;s money with no salary growth. Your real calculation adds growth, inflation, job-search time, employment probability and live salary data.</p>
      </div>
    </div>
  );
}

const topics = [
  { key: "account", tone: "lime", title: "Account and sign-in", body: "Problems signing in, with Google sign-in, or with your saved scenarios.", include: ["The email you signed up with", "What you clicked and what happened", "A screenshot, if you have one"] },
  { key: "billing", tone: "violet", title: "Billing", body: "Payments run through Stripe. Never send card details.", include: ["The email you paid with", "Plan and date of payment", "What you expected to happen"] },
  { key: "data", tone: "paper", title: "Data corrections", body: "A tuition or salary figure looks wrong? Help us fix it for everyone.", include: ["University or role", "The figure Fence shows", "A link to the official source"] },
  { key: "teams", tone: "ink", title: "Schools and advisors", body: "Using Fence with a group of students, or interested in the Teams plan.", include: ["School or organisation", "Roughly how many students", "What you want them to decide"] },
] as const;

/** Topic picker: choosing a topic shows what to include and prefills the email subject. */
export function ContactTopics({ email }: { email?: string }) {
  const [active, setActive] = useState(0);
  const topic = topics[active];
  return (
    <div className="contact-topics">
      <div className="contact-chips" role="radiogroup" aria-label="What is it about?">
        {topics.map((item, index) => (
          <button key={item.key} type="button" role="radio" aria-checked={active === index} className={`contact-chip contact-chip--${item.tone}`} onClick={() => setActive(index)}>{item.title}</button>
        ))}
      </div>
      <div className={`contact-card contact-card--${topic.tone}`} key={topic.key}>
        <h3>{topic.title}</h3>
        <p>{topic.body}</p>
        <ul>{topic.include.map((line) => <li key={line}>{line}</li>)}</ul>
        {email ? (
          <a className="site-button site-button--lime" href={`mailto:${email}?subject=${encodeURIComponent(`[Fence] ${topic.title}`)}`}>Write about this <span aria-hidden="true">→</span></a>
        ) : (
          <p className="contact-card-note">The support email is not configured yet.</p>
        )}
      </div>
    </div>
  );
}
