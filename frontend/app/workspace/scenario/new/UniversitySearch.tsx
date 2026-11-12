"use client";

import { useEffect, useId, useRef, useState } from "react";
import { workspaceFetch, type WorkspaceUniversity } from "@/lib/api/workspace";

// Answers already fetched in this session, keyed by country + query: typing back is instant.
const cache = new Map<string, WorkspaceUniversity[]>();

/** University input with suggestions from the Fence catalogue (stored copy of the open directory). */
export default function UniversitySearch({ country, value, onChange }: { country: string; value: string; onChange: (value: string) => void }) {
  const [results, setResults] = useState<WorkspaceUniversity[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [loading, setLoading] = useState(false);
  const listId = useId();
  const blurTimer = useRef<number>(0);

  useEffect(() => {
    if (!open) return;
    const key = `${country}|${value.trim().toLowerCase()}`;
    const cached = cache.get(key);
    if (cached) { setResults(cached); return; }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      const params = new URLSearchParams({ country, q: value.trim() });
      workspaceFetch<WorkspaceUniversity[]>(`/api/workspace/universities?${params}`, { signal: controller.signal })
        .then((items) => { cache.set(key, items); setResults(items); setActive(-1); })
        .catch((reason) => { if (reason.name !== "AbortError") setResults([]); })
        .finally(() => setLoading(false));
    }, 120);
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, [country, value, open]);

  function choose(university: WorkspaceUniversity) {
    onChange(university.name);
    setOpen(false);
  }

  return (
    <div className="university-search">
      <input
        value={value} role="combobox" aria-expanded={open} aria-controls={listId} aria-autocomplete="list"
        placeholder={country === "Ukraine" ? "e.g. Lviv Polytechnic" : "e.g. University of Warsaw"}
        onChange={(event) => { onChange(event.target.value); setOpen(true); }}
        onFocus={() => { window.clearTimeout(blurTimer.current); setOpen(true); }}
        onBlur={() => { blurTimer.current = window.setTimeout(() => setOpen(false), 150); }}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown") { event.preventDefault(); setActive((index) => Math.min(index + 1, results.length - 1)); }
          else if (event.key === "ArrowUp") { event.preventDefault(); setActive((index) => Math.max(index - 1, 0)); }
          else if (event.key === "Enter" && open && active >= 0 && results[active]) { event.preventDefault(); choose(results[active]); }
          else if (event.key === "Escape") setOpen(false);
        }}
      />
      {open && (results.length > 0 || loading) && (
        <ul id={listId} role="listbox" className="university-search-list">
          {results.map((university, index) => (
            <li key={university.id} role="option" aria-selected={index === active}
              className={index === active ? "is-active" : ""}
              onMouseDown={(event) => { event.preventDefault(); choose(university); }}>
              <strong>{university.name}</strong>
              <span>{[university.city, university.website?.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")].filter(Boolean).join(" · ")}</span>
            </li>
          ))}
          {loading && !results.length && <li className="is-loading">Searching the catalogue…</li>}
        </ul>
      )}
    </div>
  );
}
