const authForms = document.querySelectorAll("[data-auth-form]");

for (const form of authForms) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const mode = form.dataset.authForm;
    const errorEl = form.querySelector("[data-form-error]");
    const payload = Object.fromEntries(new FormData(form).entries());

    errorEl?.classList.add("hidden");
    try {
      const response = await fetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(Array.isArray(data.detail) ? data.detail[0].msg : data.detail || "Request failed");
      }
      const token = data.access_token || data.data?.access_token;
      if (token) {
        window.localStorage.setItem("access_token", token);
      }
      window.location.href = "/calculator";
    } catch (error) {
      if (errorEl) {
        errorEl.textContent = error instanceof Error ? error.message : "Request failed";
        errorEl.classList.remove("hidden");
      }
    }
  });
}

document.body.addEventListener("htmx:configRequest", (event) => {
  const token = window.localStorage.getItem("access_token");
  if (token) {
    event.detail.headers.Authorization = `Bearer ${token}`;
  }
});
