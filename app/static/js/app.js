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

// Theme Toggle
const themeToggleBtn = document.getElementById("theme-toggle");
if (themeToggleBtn) {
  // Check local storage for theme preference, default to light
  if (localStorage.getItem("theme") === "dark" || (!("theme" in localStorage) && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }

  themeToggleBtn.addEventListener("click", () => {
    document.documentElement.classList.toggle("dark");
    if (document.documentElement.classList.contains("dark")) {
      localStorage.setItem("theme", "dark");
    } else {
      localStorage.setItem("theme", "light");
    }
  });
}
