"use client";

import Link from "next/link";
import { useState } from "react";
import { type GoalMilestone, goalPercent } from "./goalMilestones";

/** One line for the whole goal: a small dot per step, done steps first, upcoming steps grey. */
export default function GoalProgress({ goal, milestones }: { goal: string; milestones: GoalMilestone[] }) {
  // Done steps first so the filled part of the line always ends at the last done dot.
  const ordered = [...milestones.filter((item) => item.done), ...milestones.filter((item) => !item.done)];
  const doneCount = milestones.length - milestones.filter((item) => !item.done).length;
  const percent = goalPercent(milestones);
  const next = ordered.find((item) => !item.done);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = ordered.find((item) => item.id === selectedId) ?? null;
  const fill = ordered.length > 1 ? (Math.max(doneCount - 1, 0) / (ordered.length - 1)) * 100 : 100;

  return (
    <section className="ov-goal" aria-labelledby="ov-goal-title">
      <div className="ov-goal-head">
        <div>
          <p className="ov-goal-kicker">Goal · {goal}</p>
          <h2 id="ov-goal-title">You have reached <span className="ov-goal-percent">{percent}%</span> of your goal</h2>
        </div>
        <p className="ov-goal-count"><strong>{doneCount}</strong> of {milestones.length} steps done</p>
      </div>

      <div className="ov-goal-track">
        <div className="ov-goal-line" aria-hidden="true"><span style={{ width: `${fill}%` }} /></div>
        <ol className="ov-goal-dots">
          {ordered.map((item, index) => {
            // Tips near the edges anchor to that edge so they never leave the card.
            const edge = index < ordered.length / 3 ? "is-start" : index >= (ordered.length * 2) / 3 ? "is-end" : "";
            return (
              <li key={item.id}>
                <button
                  type="button"
                  className={`ov-goal-dot ${item.done ? "is-done" : ""} ${item.id === selectedId ? "is-selected" : ""}`}
                  aria-label={`${item.done ? "Done" : "Upcoming"}: ${item.label}`}
                  aria-pressed={item.id === selectedId}
                  onClick={() => setSelectedId(item.id === selectedId ? null : item.id)}
                />
                <span className={`ov-goal-tip ${edge}`} aria-hidden="true">{item.done ? "✓ " : ""}{item.label}</span>
              </li>
            );
          })}
        </ol>
      </div>

      <p className="ov-goal-detail" aria-live="polite">
        {selected ? (
          <><strong>{selected.done ? "Done" : "Upcoming"}:</strong> {selected.label}{!selected.done && <> · <Link href={selected.href} className="ov-link">Do it now →</Link></>}</>
        ) : next ? (
          <><strong>Next step:</strong> {next.label} · <Link href={next.href} className="ov-link">Start →</Link></>
        ) : (
          <><strong>Every step is done.</strong> Review your calculations before you decide.</>
        )}
      </p>
    </section>
  );
}
