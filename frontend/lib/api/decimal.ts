/** Display helpers for API numbers (money, ROI). The API already sends plain JSON numbers. */
export function formatMoney(value: number | null | undefined, currency: string, fallback = "—"): string {
  if (value == null || !Number.isFinite(value)) return fallback;
  return new Intl.NumberFormat("en", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}

export function formatPercent(value: number | null | undefined, fallback = "N/A"): string {
  if (value == null || !Number.isFinite(value)) return fallback;
  return `${new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(value)}%`;
}
