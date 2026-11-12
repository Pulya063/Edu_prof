"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

export type SearchOption<T = unknown> = { key: string; label: string; meta?: string; data?: T };

type Props<T> = {
  value: string;
  onChange: (value: string) => void;
  onPick?: (option: SearchOption<T>) => void;
  /** A fixed list, filtered here. */
  options?: SearchOption<T>[];
  /** Or a list from the API; reloadKey says when an earlier answer stops being valid. */
  load?: (query: string, signal: AbortSignal) => Promise<SearchOption<T>[]>;
  reloadKey?: string;
  placeholder?: string;
  required?: boolean;
  loadingText?: string;
};

/** Pick from the list or type your own value: free text is always allowed. */
export default function SearchSelect<T>({ value, onChange, onPick, options, load, reloadKey = "", placeholder, required, loadingText = "Searching…" }: Props<T>) {
  const [loaded, setLoaded] = useState<SearchOption<T>[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [loading, setLoading] = useState(false);
  const listId = useId();
  const blurTimer = useRef(0);
  const cache = useRef(new Map<string, SearchOption<T>[]>());

  const filtered = useMemo(() => {
    if (!options) return loaded;
    const query = value.trim().toLowerCase();
    // A value picked earlier shows the whole list again, not only itself.
    const exact = options.some((option) => option.label.toLowerCase() === query);
    return (query && !exact ? options.filter((option) => option.label.toLowerCase().includes(query)) : options).slice(0, 40);
  }, [options, loaded, value]);

  useEffect(() => {
    if (!open || !load) return;
    const query = value.trim();
    const key = `${reloadKey}|${query.toLowerCase()}`;
    const cached = cache.current.get(key);
    if (cached) { setLoaded(cached); return; }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      load(query, controller.signal)
        .then((items) => { cache.current.set(key, items); setLoaded(items); setActive(-1); })
        .catch((reason) => { if (reason.name !== "AbortError") setLoaded([]); })
        .finally(() => setLoading(false));
    }, 150);
    return () => { controller.abort(); window.clearTimeout(timer); };
    // load is recreated each render; reloadKey carries what it depends on.
  }, [value, open, reloadKey]); // eslint-disable-line react-hooks/exhaustive-deps

  function choose(option: SearchOption<T>) {
    onChange(option.label);
    onPick?.(option);
    setOpen(false);
  }

  return (
    <div className="university-search">
      <input
        required={required} minLength={required ? 2 : undefined} value={value} placeholder={placeholder}
        role="combobox" aria-expanded={open} aria-controls={listId} aria-autocomplete="list" autoComplete="off"
        onChange={(event) => { onChange(event.target.value); setOpen(true); setActive(-1); }}
        onFocus={() => { window.clearTimeout(blurTimer.current); setOpen(true); }}
        onBlur={() => { blurTimer.current = window.setTimeout(() => setOpen(false), 150); }}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown") { event.preventDefault(); setActive((index) => Math.min(index + 1, filtered.length - 1)); }
          else if (event.key === "ArrowUp") { event.preventDefault(); setActive((index) => Math.max(index - 1, 0)); }
          else if (event.key === "Enter" && open && active >= 0 && filtered[active]) { event.preventDefault(); choose(filtered[active]); }
          else if (event.key === "Escape") setOpen(false);
        }}
      />
      {open && (filtered.length > 0 || loading) && (
        <ul id={listId} role="listbox" className="university-search-list">
          {filtered.map((option, index) => (
            <li key={option.key} role="option" aria-selected={index === active} className={index === active ? "is-active" : ""}
              onMouseDown={(event) => { event.preventDefault(); choose(option); }}>
              <strong>{option.label}</strong>
              {option.meta ? <span>{option.meta}</span> : null}
            </li>
          ))}
          {loading && !filtered.length && <li className="is-loading">{loadingText}</li>}
        </ul>
      )}
    </div>
  );
}
