"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { setDisplayCurrency } from "@/lib/api/decimal";
import { type WorkspaceState, workspaceFetch } from "@/lib/api/workspace";
import PageLoading from "./PageLoading";

type Preferences = WorkspaceState["preferences"];
type Rates = { pln_per_unit: Record<string, string>; effective_date: string | null; source_name: string };

const PreferencesContext = createContext<{ preferences: Preferences | null; rates: Rates | null; apply: (next: Preferences) => void }>({
  preferences: null, rates: null, apply: () => undefined,
});

export function useWorkspacePreferences() {
  return useContext(PreferencesContext);
}

function applyTheme(theme: string | undefined) {
  const root = document.documentElement;
  if (!theme || theme === "Fence default") delete root.dataset.wsTheme;
  else root.dataset.wsTheme = theme.toLowerCase();
}

async function loadRates(currency: string): Promise<Rates | null> {
  if (currency === "Local") return null;
  try { return await workspaceFetch<Rates>("/api/market/fx"); } catch { return null; }
}

function useRatesInFormatter(preferences: Preferences | null, rates: Rates | null) {
  const numeric = rates ? Object.fromEntries(Object.entries(rates.pln_per_unit).map(([code, value]) => [code, Number(value)])) : null;
  // Set during render so the very first paint of every page already uses the chosen currency.
  setDisplayCurrency(preferences?.currency ?? null, numeric);
}

/**
 * Applies the saved theme and display currency to the whole workspace. Pages render once both are known;
 * a change saved in Settings re-renders them.
 */
export default function WorkspacePreferences({ children }: { children: React.ReactNode }) {
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [rates, setRates] = useState<Rates | null>(null);
  const [ready, setReady] = useState(false);
  const [version, setVersion] = useState(0);
  const mounted = useRef(true);

  useRatesInFormatter(preferences, rates);

  const apply = useCallback((next: Preferences) => {
    applyTheme(next.theme);
    void loadRates(next.currency).then((nextRates) => {
      if (!mounted.current) return;
      setPreferences(next); setRates(nextRates); setVersion((value) => value + 1);
    });
  }, []);

  useEffect(() => {
    mounted.current = true;
    workspaceFetch<WorkspaceState>("/api/workspace")
      .then(async (state) => {
        applyTheme(state.preferences.theme);
        const nextRates = await loadRates(state.preferences.currency);
        if (!mounted.current) return;
        setPreferences(state.preferences); setRates(nextRates);
      })
      .catch(() => undefined)
      .finally(() => { if (mounted.current) setReady(true); });
    return () => { mounted.current = false; delete document.documentElement.dataset.wsTheme; setDisplayCurrency(null, null); };
  }, []);

  return (
    <PreferencesContext.Provider value={{ preferences, rates, apply }}>
      {ready ? <div key={version} className="workspace-preferences-scope">{children}</div> : <PageLoading label="Loading your workspace" />}
    </PreferencesContext.Provider>
  );
}
