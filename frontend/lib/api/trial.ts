import { apiRequest } from "./client";

import type { TrialProjectionOption, TrialProjectionRequest, TrialProjectionResponse, TrialShowcaseResponse } from "./generated";

// Anonymous trial calculation: the real engine on stored PL/UA data; the server saves nothing.
export type { TrialProjectionOption, TrialProjectionRequest, TrialProjectionResponse, TrialShowcaseResponse };

export const getTrialShowcase = () =>
  apiRequest<TrialShowcaseResponse>("/api/roi/preview/showcase", { fallbackMessage: "Could not load live salary data." });

export const getTrialOptions = () =>
  apiRequest<TrialProjectionOption[]>("/api/roi/preview/options", { fallbackMessage: "Could not load the available professions." });

export const runTrialProjection = (payload: TrialProjectionRequest) =>
  apiRequest<TrialProjectionResponse>("/api/roi/preview", {
    method: "POST",
    body: JSON.stringify(payload),
    fallbackMessage: "Could not calculate this scenario.",
  });
