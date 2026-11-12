"use client";

import { useState } from "react";

/* Small interactive pieces for the public sub-pages. The figures in them are fixed examples;
   real calculations live in TrialCalculator, which calls the server engine. */

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
