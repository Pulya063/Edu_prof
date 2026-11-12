"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getTrialShowcase, type TrialProjectionResponse, type TrialShowcaseResponse } from "@/lib/api/trial";

/* Every number the landing shows as real comes from one request to the deterministic engine. */
type LandingData = {
  status: "loading" | "ready" | "unavailable";
  data: TrialShowcaseResponse | null;
  scenario: (key: string) => TrialProjectionResponse | null;
};

const LandingDataContext = createContext<LandingData>({ status: "loading", data: null, scenario: () => null });

export function LandingDataProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<TrialShowcaseResponse | null>(null);
  const [status, setStatus] = useState<LandingData["status"]>("loading");

  useEffect(() => {
    let alive = true;
    getTrialShowcase()
      .then((response) => { if (alive) { setData(response); setStatus(response.careers.length ? "ready" : "unavailable"); } })
      .catch(() => { if (alive) setStatus("unavailable"); });
    return () => { alive = false; };
  }, []);

  const value = useMemo<LandingData>(() => ({
    status,
    data,
    scenario: (key) => data?.scenarios.find((item) => item.key === key)?.result ?? null,
  }), [data, status]);

  return <LandingDataContext.Provider value={value}>{children}</LandingDataContext.Provider>;
}

export const useLandingData = () => useContext(LandingDataContext);

export const formatMoney = (amount: number, currency: string) =>
  `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(amount)} ${currency}`;

export const formatYears = (months: number | null) => months === null ? "Over 10 yrs" : `${(months / 12).toFixed(1)} yrs`;

export const formatRoi = (roi: number | null) => roi === null ? "—" : `${roi >= 0 ? "+" : "−"}${Math.abs(Math.round(roi))}%`;
