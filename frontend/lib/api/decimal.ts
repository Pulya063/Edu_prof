/** Display helpers for API numbers (money, ROI). The API already sends plain JSON numbers. */

// The currency the person chose in Settings and the official rates to reach it (PLN per unit, NBP table A).
// Unset or "Local": every amount stays in its calculation's own currency.
let displayCurrency: string | null = null;
let plnPerUnit: Record<string, number> = {};

export function setDisplayCurrency(target: string | null, rates: Record<string, number> | null) {
  displayCurrency = target && target !== "Local" && rates ? target : null;
  plnPerUnit = rates ? { ...rates, PLN: 1 } : {};
}

/** value in `currency` -> [value, currency] in the chosen display currency; unchanged when no rate is known. */
export function toDisplay(value: number, currency: string): [number, string] {
  const source = currency?.toUpperCase();
  if (!displayCurrency || !source || source === displayCurrency || !plnPerUnit[source] || !plnPerUnit[displayCurrency]) return [value, currency];
  return [(value * plnPerUnit[source]) / plnPerUnit[displayCurrency], displayCurrency];
}

export function formatMoney(value: number | null | undefined, currency: string, fallback = "—"): string {
  if (value == null || !Number.isFinite(value)) return fallback;
  const [amount, code] = toDisplay(value, currency);
  return new Intl.NumberFormat("en", { style: "currency", currency: code, maximumFractionDigits: 0 }).format(amount);
}

/** ROI per year: the whole-horizon ROI spread evenly over its years (149% over 10 years shows as +14.9% / yr). */
export function formatRoiPerYear(totalPercent: number | null | undefined, years = 10, fallback = "—"): string {
  if (totalPercent == null || !Number.isFinite(totalPercent) || years <= 0) return fallback;
  const perYear = totalPercent / years;
  return `${perYear > 0 ? "+" : ""}${new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(perYear)}% / yr`;
}

export function formatPercent(value: number | null | undefined, fallback = "N/A"): string {
  if (value == null || !Number.isFinite(value)) return fallback;
  return `${new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(value)}%`;
}
