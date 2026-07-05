/* ============================================================
   app.js — основна логіка клієнтської частини
   ============================================================ */

// ── Гістограма зарплати: висота стовпчиків ───────────────────────────────────
// Запускається при завантаженні та після кожного HTMX-свопу
function initSalaryBars() {
  const bars = document.querySelectorAll('.salary-bar');
  if (!bars.length) return;
  const vals = Array.from(bars).map(b => parseFloat(b.dataset.salary));
  const max  = Math.max(...vals);
  bars.forEach(bar => {
    const pct = (parseFloat(bar.dataset.salary) / max) * 100;
    bar.style.setProperty('--bar-height', pct + '%');
  });
}

document.addEventListener('DOMContentLoaded', initSalaryBars);
document.body.addEventListener('htmx:afterSwap', initSalaryBars);

// ── Тема ───────────────────────────────────────────────────────────────────────
if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}

// Делегування подій для перемикача теми (працює після HTMX swap)
document.body.addEventListener('click', (e) => {
  const themeToggleBtn = e.target.closest('#theme-toggle');
  if (themeToggleBtn) {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }
});

// ── Динамічна навігація ──────────────────────────────────────────────────────
// ── Навігація ────────────────────────────────────────────────────────────────
// Тепер меню перемикається на сервері через Jinja {% if g.user %}

// ── Глобальна обробка кліків (Event Delegation) ────────────────────────────────
document.body.addEventListener('click', async (e) => {
  const logoutBtn = e.target.closest('#logout-btn');
  if (logoutBtn) {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch(err) {}
    window.location.href = '/';
  }
});

// Auth forms are now handled exclusively by HTMX (hx-post, hx-ext="json-enc")

// ── Фільтруємо приховані _-поля з форми перед відправкою через HTMX ──────────
document.body.addEventListener('htmx:configRequest', (e) => {
  const form = e.detail.elt?.closest('form');
  if (!form) return;
  // Видаляємо допоміжні поля, що починаються з _
  Object.keys(e.detail.parameters).forEach(key => {
    if (key.startsWith('_')) delete e.detail.parameters[key];
  });
});

// ── HTMX: Обробка помилок авторизації (401) ───────────────────────────────────
document.body.addEventListener('htmx:responseError', (e) => {
  if (e.detail.xhr.status === 401) {
    alert("Час вашої сесії вичерпано. Будь ласка, увійдіть знову.");
    window.location.href = "/login";
  }
});
// ── Університет: autocomplete ─────────────────────────────────────────────────
function initUniversityAutocomplete() {
  const input    = document.getElementById('university');
  const dropdown = document.getElementById('university-dropdown');
  const hiddenId = document.getElementById('scorecard-id');
  const hiddenCo = document.getElementById('uni-country');
  const histWrap = document.getElementById('tuition-history-wrap');

  if (!input) return;

  let debounceTimer = null;
  let activeIndex   = -1;
  let results       = [];

  // ── Debounced пошук ────────────────────────────────────────────
  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();

    // Скидаємо приховані поля при новому введенні
    hiddenId.value = '';
    hiddenCo.value = '';

    if (q.length < 2) { closeDropdown(); return; }

    debounceTimer = setTimeout(() => fetchUniversities(q), 350);
  });

  async function fetchUniversities(q) {
    showLoading();
    try {
      const res  = await fetch(`/api/roi/universities/search?q=${encodeURIComponent(q)}`);
      results    = await res.json();
      renderDropdown(results);
    } catch {
      closeDropdown();
    }
  }

  function showLoading() {
    dropdown.innerHTML = '<li class="autocomplete-loading">Пошук…</li>';
    dropdown.hidden = false;
    activeIndex = -1;
  }

  function renderDropdown(items) {
    if (!items.length) {
      dropdown.innerHTML = '<li class="autocomplete-loading">Нічого не знайдено</li>';
      dropdown.hidden = false;
      return;
    }

    dropdown.innerHTML = items.map((u, i) => {
      const isUS   = u.source === 'scorecard';
      const meta   = isUS ? `${u.city}, ${u.state}` : u.country;
      const badge  = isUS
        ? '<span class="autocomplete-item__badge">США · дані по роках</span>'
        : '<span class="autocomplete-item__badge autocomplete-item__badge--world">Світ</span>';

      return `
        <li class="autocomplete-item" role="option" data-index="${i}">
          <div>
            <p class="autocomplete-item__name">${u.name}</p>
            <p class="autocomplete-item__meta">${meta}</p>
          </div>
          ${badge}
        </li>`;
    }).join('');
    dropdown.hidden = false;
    activeIndex = -1;

    dropdown.querySelectorAll('.autocomplete-item').forEach(el => {
      el.addEventListener('click', () => selectItem(parseInt(el.dataset.index)));
    });
  }

  function selectItem(index) {
    const u = results[index];
    if (!u) return;

    input.value    = u.name;
    hiddenId.value = u.scorecard_id ?? '';
    hiddenCo.value = u.country ?? '';

    closeDropdown();
    loadTuitionHistory(u.scorecard_id, u.country, u.source);
  }

  function closeDropdown() {
    dropdown.hidden = true;
    activeIndex = -1;
  }

  // ── Клавіатурна навігація ──────────────────────────────────────
  input.addEventListener('keydown', (e) => {
    const items = dropdown.querySelectorAll('.autocomplete-item');
    if (dropdown.hidden || !items.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, items.length - 1);
      highlightItem(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      highlightItem(items);
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      selectItem(activeIndex);
    } else if (e.key === 'Escape') {
      closeDropdown();
    }
  });

  function highlightItem(items) {
    items.forEach((el, i) => {
      el.classList.toggle('autocomplete-item--active', i === activeIndex);
    });
    if (activeIndex >= 0) items[activeIndex].scrollIntoView({ block: 'nearest' });
  }

  // Закрити при кліку поза
  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      closeDropdown();
    }
  });

  // ── Вартість навчання по роках ─────────────────────────────────
  async function loadTuitionHistory(scorecardId, country, source) {
    histWrap.hidden = true;

    const params = new URLSearchParams();
    if (scorecardId) params.set('scorecard_id', scorecardId);
    if (country)     params.set('country', country);

    try {
      const res  = await fetch(`/api/roi/universities/tuition?${params}`);
      const data = await res.json();
      if (!Array.isArray(data) || !data.length) return;

      renderTuitionTable(data, source);
      histWrap.hidden = false;
    } catch { /* тихо ігноруємо */ }
  }

  function renderTuitionTable(rows, source) {
    // Джерело даних
    const sourceEl = document.getElementById('tuition-source');
    sourceEl.textContent = source === 'scorecard'
      ? '📊 Джерело: College Scorecard (Міністерство освіти США)'
      : '📋 Джерело: ОЕСР / Eurydice (середні по країні)';

    const tbody = document.getElementById('tuition-table-body');
    tbody.innerHTML = rows.map(row => {
      const cost    = row.tuition_in_state ?? row.tuition_out_of_state ?? '—';
      const net     = row.avg_net_price != null ? `$${row.avg_net_price.toLocaleString()}` : '—';
      const display = cost !== '—' ? `$${cost.toLocaleString()}` : '—';

      return `
        <tr>
          <td><strong>${row.year}</strong></td>
          <td>${display}</td>
          <td>${net}</td>
          <td>
            ${cost !== '—'
              ? `<button type="button" class="btn--xs"
                   onclick="applyTuition(${cost}, ${row.year})">Обрати</button>`
              : ''}
          </td>
        </tr>`;
    }).join('');
  }
}

document.addEventListener('DOMContentLoaded', initUniversityAutocomplete);
document.body.addEventListener('htmx:afterSwap', initUniversityAutocomplete);

// ── Глобальна функція: підставити вартість у форму ─────────────────────────
window.applyTuition = function (cost, year) {
  const costField = document.getElementById('tuition_cost');
  if (costField) {
    costField.value = cost;
    costField.focus();
    // Коротке підсвічування
    costField.style.boxShadow = '0 0 0 3px var(--clr-accent-ring)';
    setTimeout(() => { costField.style.boxShadow = ''; }, 1200);
  }
};
