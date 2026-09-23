import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent, type WheelEvent } from "react";
import { HeadlineLine } from "./motion";

type TestimonialTheme = "lime" | "light" | "dark";

type Testimonial = {
  id: string;
  quote: string;
  rating: number;
  reviewCount: number;
  name: string;
  role: string;
  initials: string;
  theme: TestimonialTheme;
  extendedStory: string;
};

const testimonials: Testimonial[] = [
  {
    id: "anna",
    quote: "The calculator showed me that the cheaper programme paid back sooner — that changed my shortlist.",
    rating: 4.9,
    reviewCount: 2184,
    name: "Anna Kowalska",
    role: "Computer Science student",
    initials: "AN",
    theme: "lime",
    extendedStory: "I compared tuition, expected salary and payback for three programmes in one evening. The result made my decision feel practical instead of emotional.",
  },
  {
    id: "mark",
    quote: "I stopped collecting random courses and finally had a weekly plan I could actually follow.",
    rating: 4.6,
    reviewCount: 1642,
    name: "Mark Chen",
    role: "Future AI engineer",
    initials: "MK",
    theme: "light",
    extendedStory: "The roadmap broke my goal into skills, projects and applications. I used it to decide what to learn next instead of starting another unfinished course.",
  },
  {
    id: "sofia",
    quote: "Seeing tuition next to salary made the trade-off clear — I chose a path that fit my budget.",
    rating: 4.3,
    reviewCount: 987,
    name: "Sofia Marin",
    role: "Business Analytics student",
    initials: "SF",
    theme: "dark",
    extendedStory: "I was choosing between a prestigious programme and a more affordable option. Seeing the payback period beside career fit helped me make a choice I could sustain.",
  },
];

function ArrowIcon({ direction }: { direction: "previous" | "next" }) {
  const isNext = direction === "next";
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" focusable="false">
      <path d={isNext ? "M5 12h14M13 6l6 6-6 6" : "M19 12H5m6 6-6-6 6-6"} stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function StarIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" fill="currentColor" focusable="false">
      <path d="m10 1.8 2.47 5.01 5.53.8-4 3.9.94 5.5L10 14.42 5.06 17l.94-5.5-4-3.9 5.53-.8L10 1.8Z" />
    </svg>
  );
}

function PlusIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg className={expanded ? "is-expanded" : ""} aria-hidden="true" viewBox="0 0 24 24" fill="none" focusable="false">
      <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

function TestimonialCard({ testimonial, index, activeIndex, expandedId, onToggle }: {
  testimonial: Testimonial;
  index: number;
  activeIndex: number;
  expandedId: string | null;
  onToggle: (id: string) => void;
}) {
  const expanded = expandedId === testimonial.id;
  const detailId = `testimonial-${testimonial.id}-details`;

  return (
    <article
      className={`testimonial-card testimonial-card--${testimonial.theme} ${activeIndex === index ? "is-active" : ""} ${expanded ? "is-expanded" : ""}`}
      data-testimonial={testimonial.id}
      aria-label={`${testimonial.name}'s student story`}
    >
      <span className="testimonial-card-quote" aria-hidden="true">“</span>
      <button
        className="testimonial-plus"
        type="button"
        aria-label={`${expanded ? "Close" : "Read"} ${testimonial.name}'s full story`}
        aria-controls={detailId}
        aria-expanded={expanded}
        onClick={() => onToggle(testimonial.id)}
      >
        <PlusIcon expanded={expanded} />
      </button>
      <blockquote><p>{testimonial.quote}</p></blockquote>
      <div className="testimonial-person">
        <span className={`testimonial-avatar testimonial-avatar--${testimonial.id}`} aria-hidden="true"><span>{testimonial.initials}</span></span>
        <span className="testimonial-person-copy"><strong>{testimonial.name}</strong><small>{testimonial.role}</small></span>
      </div>
      <div className="testimonial-expanded-copy" id={detailId} role="region" aria-label={`More from ${testimonial.name}`}>
        <p>{testimonial.extendedStory}</p>
      </div>
    </article>
  );
}

export default function TestimonialsSection({ onExplore }: { onExplore: () => void }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const swipeStart = useRef<number | null>(null);
  const wheelLocked = useRef(false);

  const move = (direction: number) => {
    setActiveIndex((current) => (current + direction + testimonials.length) % testimonials.length);
  };

  useEffect(() => {
    if (!expandedId) return;
    const closeOnEscape = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") setExpandedId(null);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [expandedId]);

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      move(-1);
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      move(1);
    }
    if (event.key === "Escape" && expandedId) {
      event.preventDefault();
      setExpandedId(null);
    }
  };

  const handlePointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (event.pointerType === "touch") swipeStart.current = event.clientX;
  };

  const handlePointerUp = (event: PointerEvent<HTMLDivElement>) => {
    if (event.pointerType !== "touch" || swipeStart.current === null) return;
    const delta = event.clientX - swipeStart.current;
    swipeStart.current = null;
    if (Math.abs(delta) < 42) return;
    move(delta > 0 ? -1 : 1);
  };

  const handleWheel = (event: WheelEvent<HTMLDivElement>) => {
    if (event.deltaX === 0 || Math.abs(event.deltaX) <= Math.abs(event.deltaY) || wheelLocked.current) return;
    event.preventDefault();
    if (Math.abs(event.deltaX) < 24) return;
    move(event.deltaX > 0 ? 1 : -1);
    wheelLocked.current = true;
    window.setTimeout(() => { wheelLocked.current = false; }, 320);
  };

  const toggleStory = (id: string) => setExpandedId((current) => current === id ? null : id);
  const activeStory = testimonials[activeIndex];

  return (
    <section
      className="motion-section testimonials-section"
      id="testimonials"
      data-header-theme="dark"
      data-motion-section="true"
      aria-labelledby="testimonials-title"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      <span className="testimonials-bg-quote testimonials-bg-quote--one" aria-hidden="true">“</span>
      <span className="testimonials-bg-quote testimonials-bg-quote--two" aria-hidden="true">”</span>
      <div className="testimonials-inner">
        <div className="testimonials-copy">
          <p className="eyebrow">07 / STUDENT STORIES</p>
          <h2 id="testimonials-title"><HeadlineLine><span className="violet-highlight">Real</span></HeadlineLine><HeadlineLine>decisions.</HeadlineLine><HeadlineLine>Real direction.</HeadlineLine></h2>
          <p className="testimonials-description">Students use Fence to compare, plan and move forward with confidence.</p>
          <div className="rating-summary" aria-label={`Rated ${activeStory.rating.toFixed(1)} out of 5 from ${activeStory.reviewCount.toLocaleString()} student reviews`}>
            <strong>{activeStory.rating.toFixed(1)} <span>/ 5</span></strong>
            <div className="rating-stars" aria-hidden="true">{Array.from({ length: 5 }, (_, index) => <StarIcon key={index} />)}</div>
            <small>from {activeStory.reviewCount.toLocaleString()} student reviews</small>
          </div>
          <div className="testimonials-controls" role="group" aria-label="Student story controls">
            <button className="testimonial-arrow testimonial-arrow--previous" type="button" aria-label="Show previous student story" onClick={() => move(-1)}><ArrowIcon direction="previous" /></button>
            <button className="testimonial-arrow testimonial-arrow--next" type="button" aria-label="Show next student story" onClick={() => move(1)}><ArrowIcon direction="next" /></button>
            <div className="testimonial-progress" aria-label="Student story selection">
              {testimonials.map((testimonial, index) => (
                <button
                  type="button"
                  key={testimonial.id}
                  className={activeIndex === index ? "is-active" : ""}
                  aria-label={`Show story ${index + 1}: ${testimonial.name}`}
                  aria-current={activeIndex === index ? "true" : undefined}
                  onClick={() => setActiveIndex(index)}
                ><span /></button>
              ))}
            </div>
          </div>
          <button className="testimonials-cta" type="button" onClick={onExplore}>Explore their paths <span aria-hidden="true"><ArrowIcon direction="next" /></span></button>
        </div>
        <div className="testimonials-stage" data-active={activeIndex} data-expanded={expandedId ?? undefined} onPointerDown={handlePointerDown} onPointerUp={handlePointerUp} onWheel={handleWheel}>
          {testimonials.map((testimonial, index) => (
            <TestimonialCard
              key={testimonial.id}
              testimonial={testimonial}
              index={index}
              activeIndex={activeIndex}
              expandedId={expandedId}
              onToggle={toggleStory}
            />
          ))}
        </div>
      </div>
      <p className="sr-only" aria-live="polite">Showing story {activeIndex + 1} of {testimonials.length}: {activeStory.name}.</p>
    </section>
  );
}
