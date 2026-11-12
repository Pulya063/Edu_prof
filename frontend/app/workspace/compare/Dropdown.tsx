"use client";

import { useEffect, useId, useRef, useState } from "react";

export type DropdownOption = { value: string; label: string };

/** A select that opens from anywhere on its button, closes on outside click or Esc, and never fills anything in itself. */
export default function Dropdown({ label, value, options, onChange, icon }: {
  label: string; value: string; options: DropdownOption[]; onChange: (value: string) => void; icon?: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const root = useRef<HTMLDivElement>(null);
  const listId = useId();
  const current = options.find((option) => option.value === value) ?? options[0];

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => { if (!root.current?.contains(event.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  function choose(option: DropdownOption) {
    onChange(option.value);
    setOpen(false);
  }

  return (
    <div className={`fence-dropdown ${open ? "is-open" : ""}`} ref={root}>
      <button type="button" className="fence-dropdown-trigger" aria-haspopup="listbox" aria-expanded={open} aria-controls={listId}
        onClick={() => { setOpen((state) => !state); setActive(options.indexOf(current)); }}
        onKeyDown={(event) => {
          if (event.key === "Escape") setOpen(false);
          else if (event.key === "ArrowDown") { event.preventDefault(); setOpen(true); setActive((index) => Math.min(index + 1, options.length - 1)); }
          else if (event.key === "ArrowUp") { event.preventDefault(); setActive((index) => Math.max(index - 1, 0)); }
          else if (event.key === "Enter" && open && options[active]) { event.preventDefault(); choose(options[active]); }
        }}>
        {icon}
        <span className="fence-dropdown-text"><small>{label}</small><strong>{current?.label}</strong></span>
        <svg className="fence-dropdown-chevron" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </button>
      {open && (
        <ul id={listId} role="listbox" aria-label={label} className="fence-dropdown-list">
          {options.map((option, index) => (
            <li key={option.value} role="option" aria-selected={option.value === value}
              className={`${option.value === value ? "is-selected" : ""} ${index === active ? "is-active" : ""}`}
              onMouseDown={(event) => { event.preventDefault(); choose(option); }}>
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
