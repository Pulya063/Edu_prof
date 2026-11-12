"use client";

import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api/client";
import type { ProjectionCostItem, ProjectionPreviewResponse, SimulationProjectionResponse } from "@/lib/api/generated";
import DecimalInput, { parseDecimal } from "../../DecimalInput";
import { Icon } from "../../WorkspaceUI";

type Projection = SimulationProjectionResponse;

const LIVING = new Set(["housing", "food", "transport", "study_materials", "other_living"]);
const DEDUCTIONS = new Set(["scholarships", "income_during_study"]);

/** Lines of the projection; a calculation saved before lines existed gets them from its breakdown. */
function linesOf(projection: Projection): ProjectionCostItem[] {
  const saved = projection.calculation_inputs.cost_items;
  if (saved?.length) return saved;
  const costs = projection.cost_breakdown;
  const line = (key: ProjectionCostItem["key"], label: string, amount: number | null | undefined, editable = true): ProjectionCostItem => (
    { key, label, amount: amount ?? 0, per_month: null, enabled: true, editable, source: "stored", source_name: null, source_url: null }
  );
  return [
    line("tuition", "Tuition", costs.tuition),
    line("mandatory_fees", "Mandatory fees", costs.mandatory_fees),
    line("other_living", "Living costs", costs.incremental_living_cost),
    line("additional_training", "Additional training and courses", costs.additional_education),
    line("scholarships", "Scholarships and grants", costs.scholarships_and_grants),
    line("pay_given_up", "Pay given up while studying", costs.baseline_income_during_study, false),
    line("income_during_study", "Income earned while studying", costs.employment_income_during_study),
  ];
}

/** Lines the person is changing, and what the unchanged engine says about them, before anything is saved. */
export function useCostLines(baseUrl: string | null, projection: Projection | null, onSaved: (saved: Projection) => void) {
  const original = useMemo(() => (projection ? linesOf(projection) : []), [projection?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const [lines, setLines] = useState(original);
  const [preview, setPreview] = useState<ProjectionPreviewResponse | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const dirty = JSON.stringify(lines) !== JSON.stringify(original);

  useEffect(() => { setLines(original); setPreview(null); setError(""); }, [original]);

  useEffect(() => {
    if (!dirty || !baseUrl) { setPreview(null); setCalculating(false); return; }
    const controller = new AbortController();
    setCalculating(true);
    const timer = window.setTimeout(() => {
      apiRequest<ProjectionPreviewResponse>(`${baseUrl}/recalculate`, {
        method: "POST", authenticated: true, signal: controller.signal,
        body: JSON.stringify({ cost_items: lines, save: false }),
        fallbackMessage: "Could not recalculate with these costs.",
      })
        .then((result) => { setPreview(result); setError(""); })
        .catch((reason) => { if (reason.name !== "AbortError") setError(reason.message); })
        .finally(() => { if (!controller.signal.aborted) setCalculating(false); });
    }, 300);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [lines, dirty, baseUrl]);

  function change(key: string, patch: Partial<ProjectionCostItem>) {
    setLines((current) => current.map((line) => line.key === key ? { ...line, ...patch } : line));
  }

  async function save() {
    if (!baseUrl) return;
    setSaving(true); setError("");
    try {
      onSaved(await apiRequest<Projection>(`${baseUrl}/recalculate`, {
        method: "POST", authenticated: true,
        body: JSON.stringify({ cost_items: lines, save: true }),
        fallbackMessage: "Could not save these costs.",
      }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save these costs.");
    } finally { setSaving(false); }
  }

  return { lines, preview, dirty, calculating, saving, error, change, save, reset: () => setLines(original) };
}

function AmountInput({ value, onChange, label }: { value: number; onChange: (value: number) => void; label: string }) {
  const [text, setText] = useState(String(value));
  const invalid = Number.isNaN(parseDecimal(text));
  // Reset or an AI suggestion changes the amount from outside.
  useEffect(() => { if ((parseDecimal(text) ?? 0) !== value) setText(String(value)); }, [value]); // eslint-disable-line react-hooks/exhaustive-deps
  return <DecimalInput aria-label={label} aria-invalid={invalid} value={text} onChange={(event) => {
    setText(event.target.value);
    const parsed = parseDecimal(event.target.value);
    if (!Number.isNaN(parsed)) onChange(parsed ?? 0);
  }} />;
}

function sourceText(line: ProjectionCostItem): string {
  if (line.source === "user" && !line.amount) return "Not entered";
  if (line.source === "country_average") return "Country average";
  if (line.source === "calculated") return "Calculated";
  if (line.source === "ai") return "AI estimate, added by you";
  if (line.source === "user") return "Your figure";
  return "Saved figure";
}

type Props = {
  editor: ReturnType<typeof useCostLines>;
  years: number;
  currency: string;
  money: (value: number | null | undefined) => string;
  costs: Projection["cost_breakdown"];
  total: number;
};

export default function CostEditor({ editor, years, currency, money, costs, total }: Props) {
  const { lines, change } = editor;
  const hasLiving = lines.some((line) => LIVING.has(line.key) && line.enabled);

  function row(line: ProjectionCostItem) {
    const monthly = line.per_month != null;
    return (
      <div key={line.key} className={`cost-line ${line.enabled ? "" : "is-off"}`}>
        <button type="button" role="switch" aria-checked={line.enabled} aria-label={`Count ${line.label}`} className="cost-switch"
          onClick={() => change(line.key, { enabled: !line.enabled })}><i aria-hidden="true" /></button>
        <div className="cost-line-label">
          <strong>{line.label}</strong>
          <small>{line.source_url ? <a href={line.source_url} target="_blank" rel="noreferrer">{sourceText(line)}</a> : sourceText(line)}</small>
        </div>
        {line.editable ? (
          <label className="cost-line-input">
            <AmountInput label={`${line.label} amount`}
              value={monthly ? line.per_month as number : line.amount}
              onChange={(value) => change(line.key, monthly
                ? { per_month: value, amount: Math.round(value * 12 * years * 100) / 100, source: "user", source_name: null, source_url: null }
                : { amount: value, source: "user", source_name: null, source_url: null })} />
            <span>{currency}{monthly ? " / month" : ""}</span>
          </label>
        ) : <span className="cost-line-input is-fixed">from income without the degree</span>}
        <strong className="cost-line-total">{DEDUCTIONS.has(line.key) && line.amount ? "− " : ""}{money(line.amount)}</strong>
      </div>
    );
  }

  const groups = [
    { title: "What you pay", items: lines.filter((line) => line.key !== "pay_given_up" && !DEDUCTIONS.has(line.key)) },
    { title: "What reduces it", items: lines.filter((line) => line.key === "scholarships" || line.key === "income_during_study") },
    { title: "What you give up", items: lines.filter((line) => line.key === "pay_given_up") },
  ];

  return (
    <section id="investment" className="sketch-card calculation-panel cost-editor">
      <div className="calculation-panel-heading">
        <Icon name="database" />
        <div><h2>Where the money goes</h2><p>Switch off what does not apply to you, or type your own amount. The whole page follows.</p></div>
      </div>
      {groups.map((group) => group.items.length ? (
        <div className="cost-group" key={group.title}>
          <h3>{group.title}</h3>
          {group.items.map(row)}
        </div>
      ) : null)}
      {hasLiving ? <p className="calculation-note">You would pay for most food and housing without studying too. Switch those lines off to count only what the study itself costs.</p> : null}
      <div className="calculation-lines cost-editor-totals">
        <div><span>Direct cost</span><strong>{money(costs.net_direct_cost)}</strong></div>
        <div><span>Pay given up, after income while studying</span><strong>{money(costs.opportunity_cost)}</strong></div>
        <div className="is-total"><span>Total investment</span><strong>{money(total)}</strong></div>
      </div>
      {editor.dirty || editor.error ? (
        <div className="cost-editor-bar" role="status">
          <span>{editor.error || (editor.calculating ? "Recalculating…" : "Preview with your changes. Not saved yet.")}</span>
          <button type="button" className="sketch-btn" onClick={editor.reset} disabled={editor.saving}>Reset</button>
          <button type="button" className="sketch-btn sketch-btn-primary" onClick={() => void editor.save()} disabled={editor.saving || !editor.dirty}>{editor.saving ? "Saving…" : "Save changes"}</button>
        </div>
      ) : null}
    </section>
  );
}
