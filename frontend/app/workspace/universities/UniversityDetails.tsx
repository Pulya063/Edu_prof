"use client";

import { Icon } from "../WorkspaceUI";
import type { WorkspaceUniversityDetails } from "@/lib/api/workspace";
import type { UniversityFeeItem, UniversityFees } from "@/lib/api/generated";
import "../../styles/university-profile.css";

const PERIOD_LABEL: Record<string, string> = { year: "per year", semester: "per semester", month: "per month", unknown: "period not stated" };
const KIND_LABEL: Record<string, string> = {
  admissions: "Admissions", scholarships: "Scholarships", fees: "Fees", sport: "Sport", faculties: "Faculties", international: "International", news: "News",
};

function money(value: number | null | undefined, currency: string | null | undefined) {
  if (value == null) return "—";
  return currency
    ? new Intl.NumberFormat("en", { style: "currency", currency, maximumFractionDigits: 0 }).format(value)
    : new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(value);
}

function shortDate(value: string | null | undefined) {
  return value ? new Intl.DateTimeFormat("en", { day: "numeric", month: "short", year: "numeric" }).format(new Date(value)) : "";
}

function host(url: string) {
  return url.replace(/^https?:\/\/(www\.)?/, "").split("/")[0];
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="uprof-empty">{children}</p>;
}

function feeLabel(item: UniversityFeeItem) {
  return [item.programme, item.faculty, item.study_mode].filter(Boolean).join(" · ");
}

function FeeRange({ fees }: { fees: UniversityFees }) {
  return (
    <div className="uprof-fees">
      <strong className="uprof-fees-range">{money(fees.min_per_year, fees.currency)} – {money(fees.max_per_year, fees.currency)} <small>per year, {fees.academic_year}</small></strong>
      <dl>
        <div><dt>Cheapest</dt><dd>{feeLabel(fees.cheapest)}</dd></div>
        <div><dt>Most expensive</dt><dd>{feeLabel(fees.most_expensive)}</dd></div>
      </dl>
      <p>{fees.paid_programme_count} paid programmes{fees.free_programme_count ? `, ${fees.free_programme_count} without a fee` : ""}. {fees.source_kind === "press" ? "Published price list, not the original order: check with the university before paying." : "Copied from the official document."} Full-time state-funded places are free and are not in this range.</p>
      <details>
        <summary>All {fees.paid_programme_count} programmes</summary>
        <ul>{fees.programmes.map((item, index) => <li key={`${item.programme}-${index}`}><span>{feeLabel(item)}{item.level ? ` · ${item.level}` : ""}</span><b>{money(item.amount_per_year, fees.currency)}</b></li>)}</ul>
      </details>
      <a className="uprof-link" href={fees.source_url} target="_blank" rel="noreferrer">{fees.source_title} ↗</a>
    </div>
  );
}

/** University profile body, shared by the full page and the compare side panel. */
export default function UniversityDetails({ university, compact = false }: { university: WorkspaceUniversityDetails; compact?: boolean }) {
  const profile = university.profile;
  const facts = profile?.facts;
  const pages = profile?.official_pages ?? [];
  const pagesOf = (kind: string) => pages.filter((page) => page.kind === kind);
  const heroImage = facts?.image_url || profile?.gallery[0]?.thumb_url;
  const tuitionMentions = profile?.tuition_mentions ?? [];

  const verified = university.verified_facts;
  const fees = verified?.fees;
  const address = verified?.address;
  const faculties = verified?.faculties.length ? verified.faculties : profile?.faculties ?? [];
  const addressText = address ? [address.street, [address.postal_code, address.city].filter(Boolean).join(" ")].filter(Boolean).join(", ") : facts?.city || "—";

  const tiles = [
    { label: "Founded", value: facts?.founded || verified?.founded || "—" },
    { label: "Address", value: addressText },
    { label: "Faculties", value: faculties.length ? String(faculties.length) : verified?.programme_count ? `${verified.programme_count} programmes` : "—" },
    { label: "Tuition per year", value: fees ? `${money(fees.min_per_year, fees.currency)} – ${money(fees.max_per_year, fees.currency)}` : university.annual_tuition != null ? money(university.annual_tuition, university.currency) : tuitionMentions.length ? "See fees" : "Not published" },
  ];

  return (
    <div className={`uprof ${compact ? "is-compact" : ""}`}>
      <section className="uprof-hero">
        {heroImage ? <img className="uprof-hero-image" src={heroImage} alt="" /> : <div className="uprof-hero-image is-blank" aria-hidden="true">{university.name.split(/\s+/).map((part) => part[0]).join("").slice(0, 3)}</div>}
        <div className="uprof-hero-copy">
          <div className="uprof-chips">
            <span className="uprof-chip is-lime">{university.country}</span>
            {facts?.city && <span className="uprof-chip">{facts.city}</span>}
            <span className="uprof-chip is-outline">{profile?.status === "ready" ? "Rich public profile" : profile?.status === "partial" ? "Partial public profile" : "Directory record"}</span>
          </div>
          <h2>{university.program_name || university.name}</h2>
          <p>{profile?.summary || university.description || "No public summary was found. The official website below is the primary source."}</p>
          <div className="uprof-hero-actions">
            {university.website && <a className="uprof-btn is-primary" href={university.website} target="_blank" rel="noreferrer">Official website <Icon name="arrow" size={16} /></a>}
            {profile?.summary_source_url && <a className="uprof-btn" href={profile.summary_source_url} target="_blank" rel="noreferrer">Wikipedia</a>}
          </div>
        </div>
      </section>

      <div className="uprof-tiles">
        {tiles.map((tile, index) => <div key={tile.label} className={`uprof-tile tone-${index}`}><span>{tile.label}</span><strong>{tile.value}</strong></div>)}
      </div>

      <div className="uprof-grid">
        <section className="uprof-card is-wide">
          <header><span className="uprof-icon is-lime"><Icon name="graduation" size={20} /></span><div><h3>Faculties{faculties.length ? ` (${faculties.length})` : ""}</h3><p>{verified?.faculties_source ? `From the official register, ${verified.faculties_source}.` : "From Wikidata or the official faculties page."}</p></div></header>
          {faculties.length ? <div className="uprof-tags">{faculties.map((faculty) => <span key={faculty}>{faculty}</span>)}</div> : <Empty>No faculty list was found in public sources.</Empty>}
          {pagesOf("faculties").map((page) => <a key={page.url} className="uprof-link" href={page.url} target="_blank" rel="noreferrer">{page.title} ↗</a>)}
        </section>

        <section className="uprof-card">
          <header><span className="uprof-icon is-violet"><Icon name="document" size={20} /></span><div><h3>Admission documents</h3><p>Copied from the official admissions pages.</p></div></header>
          {university.documents.map((document) => <a key={document.id} className="uprof-row" href={document.source_url} target="_blank" rel="noreferrer"><strong>{document.title}</strong><span>{document.subject_name}</span></a>)}
          {profile?.admission_documents.length ? <ul className="uprof-list">{profile.admission_documents.map((item) => <li key={item.text}>{item.text}</li>)}</ul> : !university.documents.length && <Empty>The admissions page does not list documents in a readable form.</Empty>}
          {pagesOf("admissions").map((page) => <a key={page.url} className="uprof-link" href={page.url} target="_blank" rel="noreferrer">{page.title} ↗</a>)}
        </section>

        <section className="uprof-card">
          <header><span className="uprof-icon is-ink"><Icon name="wallet" size={20} /></span><div><h3>Tuition & fees</h3><p>Amounts parsed from official fee pages — verify before paying.</p></div></header>
          {fees && <FeeRange fees={fees} />}
          {university.programmes.map((programme) => <div key={programme.id} className="uprof-row"><strong>{programme.name}</strong><span>{money(programme.tuition_cost, university.currency)} / year · {programme.duration_years} years</span></div>)}
          {tuitionMentions.map((item, index) => <div key={`${item.source_url}-${index}`} className="uprof-amount"><strong>{money(item.amount, item.currency)}</strong><span>{PERIOD_LABEL[item.period]}</span><p>{item.text}</p></div>)}
          {!fees && !university.programmes.length && !tuitionMentions.length && <Empty>No fee amounts are published as text. Fees are often in PDF regulations on the fees page.</Empty>}
          {pagesOf("fees").map((page) => <a key={page.url} className="uprof-link" href={page.url} target="_blank" rel="noreferrer">{page.title} ↗</a>)}
        </section>

        <section className="uprof-card">
          <header><span className="uprof-icon is-lime"><Icon name="star" size={20} /></span><div><h3>Scholarships</h3><p>Funding mentioned by the university.</p></div></header>
          {university.scholarships.map((scholarship) => <div key={scholarship.id} className="uprof-row"><strong>{scholarship.name}</strong><span>{scholarship.amount != null ? money(scholarship.amount, scholarship.currency) : scholarship.eligibility || ""}</span></div>)}
          {profile?.scholarship_mentions.length ? <ul className="uprof-list">{profile.scholarship_mentions.map((item) => <li key={item.text}>{item.text}</li>)}</ul> : !university.scholarships.length && <Empty>No scholarship details were found on the official pages.</Empty>}
          {pagesOf("scholarships").map((page) => <a key={page.url} className="uprof-link" href={page.url} target="_blank" rel="noreferrer">{page.title} ↗</a>)}
        </section>

        <section className="uprof-card">
          <header><span className="uprof-icon is-violet"><Icon name="trophy" size={20} /></span><div><h3>Sport & student life</h3><p>Sport clubs and facilities on the official site.</p></div></header>
          {profile?.sport_mentions.length ? <ul className="uprof-list">{profile.sport_mentions.map((item) => <li key={item.text}>{item.text}</li>)}</ul> : <Empty>No sport section was found on the official website.</Empty>}
          {[...pagesOf("sport"), ...pagesOf("international")].map((page) => <a key={page.url} className="uprof-link" href={page.url} target="_blank" rel="noreferrer">{KIND_LABEL[page.kind]}: {page.title} ↗</a>)}
        </section>

        <section className="uprof-card is-wide">
          <header><span className="uprof-icon is-lime"><Icon name="bell" size={20} /></span><div><h3>Latest news</h3><p>Headlines as published, newest first.</p></div></header>
          {profile?.news.length ? <div className="uprof-news">{profile.news.map((item) => <a key={item.url} href={item.url} target="_blank" rel="noreferrer"><span>{[item.source, shortDate(item.published_at)].filter(Boolean).join(" · ")}</span><strong>{item.title}</strong></a>)}</div> : <Empty>No recent news found.</Empty>}
        </section>

        {profile?.videos.length ? (
          <section className="uprof-card is-wide">
            <header><span className="uprof-icon is-ink"><Icon name="play" size={20} /></span><div><h3>Videos</h3><p>Latest uploads from the university YouTube channel.</p></div></header>
            <div className="uprof-news">{profile.videos.map((video) => <a key={video.url} href={video.url} target="_blank" rel="noreferrer"><span>YouTube · {shortDate(video.published_at)}</span><strong>{video.title}</strong></a>)}</div>
          </section>
        ) : null}

        <section className="uprof-card is-wide">
          <header><span className="uprof-icon is-violet"><Icon name="image" size={20} /></span><div><h3>Gallery</h3><p>Openly licensed photos from Wikimedia Commons.</p></div></header>
          {profile?.gallery.length ? <div className="uprof-gallery">{profile.gallery.map((image) => <a key={image.url} href={image.source_url || image.url} target="_blank" rel="noreferrer"><img src={image.thumb_url} alt={image.title} loading="lazy" /></a>)}</div> : <Empty>No openly licensed photos are available yet.</Empty>}
        </section>
      </div>

      <footer className="uprof-sources">
        <span>Sources</span>
        {profile?.sources.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.title} · {host(source.url)}</a>)}
        {profile?.unavailable_sources.map((note) => <em key={note}>{note}</em>)}
        {profile?.fetched_at && <small>Collected {shortDate(profile.fetched_at)}</small>}
      </footer>
    </div>
  );
}
