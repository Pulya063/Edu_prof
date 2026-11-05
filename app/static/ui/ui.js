// Fence quick UI: thin client over the JSON API (cookie auth + double-submit CSRF).
(function () {
  const flash = document.getElementById("flash");
  const showError = (message) => { flash.textContent = message; flash.hidden = false; window.scrollTo({ top: 0, behavior: "smooth" }); };

  function csrf() {
    const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  async function api(method, url, body) {
    const headers = { "Accept": "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (method !== "GET") headers["X-CSRF-Token"] = csrf();
    const response = await fetch(url, { method, headers, credentials: "same-origin", body: body === undefined ? undefined : JSON.stringify(body) });
    let data = null;
    try { data = await response.json(); } catch { /* empty body */ }
    if (!response.ok) {
      let detail = data && data.detail;
      if (Array.isArray(detail)) detail = detail.map((e) => `${(e.loc || []).join(".")}: ${e.msg}`).join("; ");
      throw new Error(detail || `Помилка ${response.status}`);
    }
    return data;
  }

  const busy = (button, on, label) => { if (!button) return; button.disabled = on; if (on) { button.dataset.label = button.textContent; button.textContent = label || "Зачекай…"; } else if (button.dataset.label) { button.textContent = button.dataset.label; } };

  // Tabs on the login page
  document.querySelectorAll("[data-tab]").forEach((tab) => tab.addEventListener("click", () => {
    document.querySelectorAll("[data-tab]").forEach((t) => t.classList.toggle("is-active", t === tab));
    document.querySelectorAll("[data-auth]").forEach((form) => { form.hidden = form.dataset.auth !== tab.dataset.tab; });
  }));

  // Login / register
  document.querySelectorAll("[data-auth]").forEach((form) => form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button[type=submit]");
    busy(button, true);
    try {
      const body = Object.fromEntries(new FormData(form));
      await api("POST", `/api/auth/${form.dataset.auth}`, body);
      window.location.href = "/ui/";
    } catch (error) { showError(error.message); busy(button, false); }
  }));

  // Logout
  document.querySelectorAll("[data-logout]").forEach((button) => button.addEventListener("click", async () => {
    try { await api("POST", "/api/auth/logout"); } catch { /* cookies may already be gone */ }
    window.location.href = "/ui/login";
  }));

  // New scenario + projection
  const newForm = document.querySelector("[data-new-scenario]");
  if (newForm) newForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const f = Object.fromEntries(new FormData(newForm));
    const button = newForm.querySelector("button[type=submit]");
    busy(button, true, "Рахуємо…");
    const list = (value) => (value || "").split(",").map((s) => s.trim()).filter(Boolean);
    const num = (value) => (value === "" || value == null ? "0" : String(value));
    try {
      const scenario = await api("POST", "/api/simulations", {
        name: f.name,
        assumptions: {
          university: f.university, specialization: f.specialization, country: f.country, degree: f.degree,
          currency: f.currency, annual_tuition: num(f.annual_tuition), study_duration_years: num(f.study_duration_years),
          career_target: f.career_target, existing_skills: list(f.existing_skills), additional_education: [],
          courses: [], certifications: [], experience_years: num(f.experience_years),
        },
      });
      const evidence = (metric, role) => ({
        metric, source_name: f.source_name, source_reference: f.source_reference, acquired_at: new Date().toISOString(),
        country: f.country, role, seniority: f.seniority, currency: f.currency, confidence: f.confidence,
      });
      const baseline = Number(f.baseline_annual_salary || 0);
      const projection = {
        annual_start_salary: num(f.annual_start_salary), baseline_annual_salary: num(f.baseline_annual_salary),
        annual_salary_growth_percent: num(f.annual_salary_growth_percent), baseline_salary_growth_percent: num(f.baseline_salary_growth_percent),
        foregone_income_percent: num(f.foregone_income_percent), horizon_years: Number(f.horizon_years || 10),
        mandatory_fees: num(f.mandatory_fees), additional_education_cost: num(f.additional_education_cost),
        incremental_living_cost: num(f.incremental_living_cost), scholarships_and_grants: num(f.scholarships_and_grants),
        evidence: [evidence("target_start_salary", f.career_target), ...(baseline > 0 ? [evidence("baseline_salary", "Current employment")] : [])],
      };
      if (Number(f.employment_income_during_study || 0) > 0) projection.employment_income_during_study = num(f.employment_income_during_study);
      try {
        await api("POST", `/api/simulations/${scenario.id}/revisions/${scenario.current_revision_number}/projections`, projection);
      } catch (error) {
        // Scenario is saved; carry the reason so the page can explain the missing projection.
        window.location.href = `/ui/scenarios/${scenario.id}?error=${encodeURIComponent(error.message)}`;
        return;
      }
      window.location.href = `/ui/scenarios/${scenario.id}`;
    } catch (error) { showError(error.message); busy(button, false); }
  });

  // AI review: run + poll
  const ai = document.querySelector("[data-ai]");
  if (ai) {
    const base = `/api/simulations/${ai.dataset.scenario}/revisions/${ai.dataset.revision}/projections`;
    const statusChip = ai.querySelector("[data-ai-status]");
    const runButton = ai.querySelector("[data-ai-run]");
    let attempts = 0;
    const poll = async () => {
      attempts += 1;
      try {
        const items = await api("GET", base);
        const current = (items || []).find((item) => String(item.id) === ai.dataset.projection);
        const status = current && current.ai_review ? current.ai_review.status : "not_configured";
        statusChip.textContent = status;
        if (status === "pending" || status === "running") { if (attempts < 60) setTimeout(poll, 4000); return; }
        window.location.reload();
      } catch (error) { showError(error.message); }
    };
    if (["pending", "running"].includes(ai.dataset.status)) setTimeout(poll, 4000);
    runButton.addEventListener("click", async () => {
      busy(runButton, true, "Запускаю…");
      try {
        const updated = await api("POST", `${base}/${ai.dataset.projection}/ai-review`);
        const status = updated.ai_review ? updated.ai_review.status : "not_configured";
        statusChip.textContent = status;
        if (status === "pending" || status === "running") { ai.querySelector("[data-ai-body]").innerHTML = '<p class="pulse">Агент перевіряє розрахунок…</p>'; attempts = 0; setTimeout(poll, 4000); }
        else { window.location.reload(); }
      } catch (error) { showError(error.message); busy(runButton, false); }
    });
  }
})();
