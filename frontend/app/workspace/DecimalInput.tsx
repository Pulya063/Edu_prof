"use client";

import type { InputHTMLAttributes } from "react";

/** "1 250,5" -> 1250.5; blank -> null; anything else -> NaN so the caller can report it. */
export function parseDecimal(text: string): number | null {
  const clean = text.trim().replace(/\s/g, "").replace(",", ".");
  if (!clean) return null;
  const value = Number(clean);
  return Number.isFinite(value) ? value : NaN;
}

/** A number field that takes a comma or a dot, on any keyboard. */
export default function DecimalInput({ onChange, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      type="text"
      inputMode="decimal"
      autoComplete="off"
      onChange={(event) => {
        event.target.value = event.target.value.replace(/[^\d.,\s]/g, "");
        onChange?.(event);
      }}
    />
  );
}
