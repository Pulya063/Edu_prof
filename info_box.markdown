# Fence — актуальний контекст продукту й архітектури

> Phase 0 baseline: 2026-09-30. Цей розділ є канонічним описом поточної реалізації. Живий код і перевірена runtime-поведінка мають пріоритет. Старі нотатки нижче збережені лише як історичний контекст і не повинні використовуватися як доказ наявної функціональності.

## Статуси

- **Current** — присутнє в живому коді.
- **Planned** — погоджений напрям, але ще не реалізований.
- **Implemented but unverified** — код внесений, але відповідна runtime/test перевірка ще не пройдена.
- **Verified** — відповідна автоматизована або браузерна перевірка пройдена в канонічному checkout.

## Current: продукт

Fence зараз складається з редакційного Next.js-лендінгу, authenticated scenario workspace та Flask API. Backend має versioned scenario/projection foundation, а workspace уже підтримує створення education-to-career сценарію і читання результату; landing simulation, legacy ROI analysis і roadmap досі не під'єднані до цього контуру.

Основний цільовий шлях продукту:

```text
Education
→ Career
→ Financial outcome
→ Skills gap
→ Roadmap
→ Courses / projects / experience
→ Employment readiness
```

## Current: frontend

- Основний UI: `frontend/`, Next.js 14 App Router, React 18 і TypeScript.
- Реальні routes: `/`, `/plans`, `/payment`, `/contact`, `/legal/[document]`, `/login`, `/register`, `/reset-password`, `/workspace/overview`, `/workspace/scenario/new`, `/workspace/scenarios`, `/workspace/scenarios/[id]`, `/workspace/profile`, `/workspace/compare`, `/workspace/roadmap`, `/workspace/roadmap/simulation`, `/workspace/roadmap/plan`, `/workspace/courses` і `/workspace/settings`.
- Workspace overview, scenario creation/list/detail та profile використовують поточні API або реальні локальні дані. Compare, roadmap dashboard/simulation/plan, course search і settings зараз є demo UI surfaces за наданими ескізами; їхні майбутні серверні mutations та зовнішні provider connections ще не реалізовані.
- Landing page містить локальну client-side симуляцію та hardcoded university/career/scholarship/roadmap data. Вона не викликає Flask ROI API; authenticated workspace використовує simulation contracts для створення сценарію, deterministic projection і read-only overview.
- `/payment` і legal content залишаються placeholders.
- Jinja/HTMX не є основним frontend. Flask templates зберігаються лише як legacy/local diagnostic surface.
- Візуальна основа: editorial composition, `#171819`, white, lime `#B7FF2A`, violet `#D7C7FF`, сильна типографіка та purposeful motion.

## Current: backend

- Python 3.13, Flask, Pydantic, SQLAlchemy 2, PostgreSQL та Alembic у modular-monolith структурі.
- Redis зберігає refresh tokens; RabbitMQ/Celery виконує email jobs.
- Основні API:
  - auth: `/api/auth/me`, `/register`, `/login`, `/refresh`, `/logout`, `/password-reset-request`, `/password-reset`, `/login/google`, `/callback/google`;
  - ROI: `/api/roi/trial`, legacy read-only `/history`, `/trash`, delete/restore, university search і tuition history; `/analyze` retired з `410 Gone`;
  - simulations: `POST/GET /api/simulations`, `GET /api/simulations/<id>`, `POST /api/simulations/<id>/revisions`, `POST/GET /api/simulations/<id>/revisions/<number>/projections`, `GET /api/simulations/<id>/revisions/<number>/projections/<projection_id>/explainability`;
  - market: `POST /api/market/snapshots` для admin ingestion, `GET /api/market/snapshots` і `GET /api/market/snapshots/<id>` для authenticated reads;
  - roadmap: `/roadmap/`, `/roadmap/generate` та дубльований `/api/roadmap/*` namespace;
  - mail: `/api/mail/university-letter`;
  - health: `/health`.
- Основні models: `User`, `University`, `UniversityDocument`, `UniversityScholarship`, `TuitionPrice`, `EducationProgram`, `SalaryStatistic`, `CareerForecast`, `CareerAnalysis` та його normalized children, `ROICalculation`, `UserRoadmap`, `SimulationScenario`, `SimulationRevision`, `SimulationProjection`, `MarketSnapshot`, `Partner`, `MotivationLetter`.
- `CareerAnalysis`, його `CareerROI` child і legacy `ROICalculation` збережені для історії; нові фінансові результати створюються лише через `SimulationProjection`.
- Roadmap зберігається як opaque JSON і не має normalized tasks, skill evidence або feedback loop.
- Phase 0 не змінював database schema. Phase 1 додає окремі versioned simulation scenarios без зміни legacy ROI/roadmap tables.

## Current: calculations, data and AI

- Core ROI arithmetic виконується Python code, але поточна methodology залишається спрощеною.
- Active salary lookup використовує локальний CSV, O*NET за наявності credentials і country multipliers; це не повноцінний market snapshot pipeline.
- LLM використовується для qualitative insights. Він не повинен бути джерелом tuition, salary, ROI, payback, inflation або інших deterministic financial values.
- Chroma/Ollama/LangChain присутні як експериментальна AI/RAG інфраструктура; auditable ingestion, document versioning і citation pipeline ще відсутні.
- University data використовує College Scorecard і Hipolabs синхронно; кешування та scheduled refresh pipeline відсутні.
- DreamWork roadmap generation є синхронною зовнішньою інтеграцією зі спільним service account.

## Verified: Phase 0 security

- Password reset переведено на одноразовий opaque token у Redis із TTL 15 хвилин.
- Cookie-authenticated mutations захищені double-submit CSRF token.
- Sensitive auth endpoints мають Redis-backed rate limits із test-memory backend і fail-open logging при storage outage.
- Google OAuth ініціалізується під час Flask startup і повертає контрольований `503`, якщо credentials відсутні.
- `/resources` і `/api/resources` реєструються лише через `ENABLE_RESOURCE_AUDIT=true` у non-production; `/health` залишається мінімальним.
- `OAUTH_SUCCESS_URL` за потреби задає точний frontend redirect після Google callback; fallback — корінь `FRONTEND_URL`.
- Targeted Phase 0 tests і офіційний backend suite з каталогу `tests/` пройшли в канонічному checkout 2026-09-30.

## Verified: Phase 1 simulation foundation

- `SimulationScenario` є user-owned контейнером рішення з коротким summary поточного стану.
- `SimulationRevision` зберігає незмінний numbered snapshot assumptions, methodology version і references на майбутні source snapshots.
- Authenticated API дозволяє створити, перелічити й прочитати власні сценарії та додати нову ревізію.
- Поточний зріз не обчислює salary, ROI, payback, demand або readiness і не під'єднаний до landing simulation чи roadmap.
- Targeted simulation/migration checks і повний backend suite пройшли в канонічному checkout 2026-09-30; міграцію створено, але не застосовано до користувацької бази даних.

## Verified: Phase 2 deterministic projection foundation

- Кожна проєкція належить конкретній immutable scenario revision і зберігає methodology version та canonical input fingerprint.
- Financial engine є чистим deterministic code: direct education cost, opportunity cost, salary trajectory, incremental earnings, payback і horizon ROI.
- Payback рахується від приросту доходу проти явного counterfactual; повтор однакових inputs не створює дубльованих результатів.
- Salary evidence має source/reference, acquisition time, country, role, seniority, currency, sample size та confidence; невкриті джерелами assumptions повертаються явно.
- Цей етап не завантажує market data автоматично та не використовує LLM для фінансових значень.
- Targeted projection/migration checks пройшли в канонічному checkout 2026-09-30; нову міграцію не застосовано до користувацької бази даних.

## Verified: Calculation Foundation v2

- `simulation_projections` є канонічним сховищем нових фінансових прогнозів; legacy `career_roi` залишається read-only історією і не переписується під нову методологію.
- `POST /api/roi/analyze` більше не створює `CareerAnalysis/CareerROI`: authenticated request повертає `410 Gone` і посилання на versioned simulation endpoints.
- Методологія `scenario-projection-v2` зберігає resolved `calculation_inputs`, деталізований `cost_breakdown` і окремий `payback_from_enrollment_months`; існуючий `payback_months` означає окупність після завершення навчання.
- Direct cost враховує tuition, mandatory fees, additional education, incremental living costs та scholarships/grants. Opportunity cost може опційно зменшуватися на загальний дохід під час навчання.
- Employment during study не є обов'язковим припущенням: незаповнене поле дорівнює нулю і доступне лише в розгорнутому detailed analysis.
- Від'ємна різниця між target і baseline salary більше не обрізається до нуля, тому слабші роки зменшують cumulative earnings та не завищують ROI.
- Нові колонки додає additive Alembic revision `b6c7d8e9f0a1`; локальна development БД оновлена до цього єдиного head 2026-10-02.
- Focused simulation/market tests: 4 passed; TypeScript `--noEmit` пройшов 2026-10-02. Повний backend suite і browser QA не запускалися.

## Verified: Phase 3 market snapshot foundation

- `MarketSnapshot` зберігає normalized annual salary range, vacancy count, demand index, snapshot/acquisition dates, source references, sample size, confidence, methodology version і canonical fingerprint.
- Лише admin може додавати validated snapshots; повтор однакового payload є ідемпотентним.
- Authenticated users можуть фільтрувати snapshots за role, country, seniority і currency.
- Deterministic projection може брати median salary із validated snapshot та зберігає `source_snapshot_refs`; manual salary input залишається сумісним fallback із обов'язковим evidence.
- Fetcher/parser/background refresh ще не реалізовані: цей етап створює стабільний storage та API contract без scraping або LLM.
- Targeted market/simulation/migration checks пройшли в канонічному checkout 2026-09-30; міграцію створено, але не застосовано до користувацької бази даних.
- Повний backend suite після Phase 3: 33 passed.

## Verified: Phase 4 forecast source resolution

- Projection request може явно задати policy для автоматичного підбору market snapshot: seniority, `as_of_date`, максимальний вік і мінімальний confidence.
- Resolver використовує лише validated `gross_annual` snapshots із точним збігом role, country, seniority та currency; вибір детермінований за freshness, confidence, sample size і стабільним tie-breaker.
- Явний `market_snapshot_id` додатково перевіряється на відповідність career target і salary basis сценарію.
- Якщо сумісного snapshot немає, API повертає контрольований `422`; manual salary fallback як і раніше потребує повного evidence.
- Етап не додає нової таблиці, міграції, fetcher, background job або frontend integration.
- Focused market/projection tests пройшли в канонічному checkout 2026-10-01; повний backend suite на цьому етапі не запускався.

## Verified: Phase 5 forecast trust contract

- Для кожної projection додано authenticated explainability endpoint у межах її scenario revision.
- Контракт явно повідомляє, що фінансовий розрахунок deterministic і не AI-generated, та повертає methodology version, salary basis і використану salary metric.
- Для snapshot-based прогнозу повертаються повний normalized snapshot, первинні source references/URLs, acquisition/snapshot dates, confidence, sample size, age in days і фактично вибране median value.
- Для manual fallback повертаються його evidence та явний `manual_evidence` source kind.
- Пошкоджені або відсутні snapshot references не приховуються: відповідь має `source_integrity` і `missing_source_snapshot_refs`.
- Етап не змінює database schema, формули, market data або frontend.
- Focused market/projection tests: 3 passed у канонічному checkout 2026-10-01; повний backend suite не запускався.

## Verified: Phase 6 analytical report integration

- Додано `GET /api/simulations/overview`: один authenticated read-model повертає останній active scenario, current revision, latest projection та explainability без frontend request waterfall.
- Next.js route `/workspace/overview` показує Education → Career → Outcome як інтерактивний аналітичний звіт, а не набір рівнозначних dashboard cards.
- Report показує investment, start salary, payback, horizon ROI, market demand, salary trajectory, methodology, confidence, sample size, freshness, source URL та unverified assumptions.
- Реалізовані loading, empty, scenario-only, unauthorized і controlled error states; landing CTAs не активувалися, pricing залишається єдиним робочим navigation CTA.
- Responsive layout перевірено у browser на desktop і 390×844 mobile viewport; console errors/warnings не виявлено, reduced-motion і keyboard focus states передбачені в CSS.
- Під час інтеграційного QA виправлено `500` при stale refresh-cookie та недоступному Redis: API тепер очищає auth/CSRF cookies і повертає контрольований unauthenticated state.
- Focused backend checks: 4 passed; TypeScript `--noEmit` пройшов. Повний backend suite і production build не запускалися.

## Verified: Phase 7 scenario creation flow

- Додано authenticated route `/workspace/scenario/new` з послідовним assumption ledger: Education → Career → Investment → Baseline → Forecast.
- Flow спочатку перевіряє session і CSRF cookie, створює immutable scenario revision через `POST /api/simulations`, а потім запитує deterministic projection через policy-based `market_snapshot_selection`.
- Target salary не генерується LLM: поле manual estimate є необов'язковим low-confidence override; якщо воно порожнє, потрібен validated market snapshot з відповідними role, country, currency і seniority. За відсутності snapshot сценарій зберігається, а UI показує контрольований partial-success стан.
- Annual tuition вводиться користувачем явно. Regional public/private ranges показуються лише як orientation і не підставляються в projection як evidence.
- Detailed financial analysis містить необов'язкові baseline, foregone income, total income during study, fees, scholarships, extra education, living costs і growth assumptions; базовий flow не вимагає їх заповнення.
- Ненульовий baseline salary вимагає provenance evidence (source, reference, acquisition date, confidence); financial outputs залишаються відповідальністю versioned deterministic service.
- Workspace navigation активує лише реалізовані Overview і Build scenario; Forecast та Roadmap залишаються позначеними як недоступні. Landing CTA/deep links не активувалися.
- Scenario builder візуально узгоджений з наданими Fence workspace ескізами: компактний app shell, біла панель inputs, темна sticky forecast surface, lime лише для primary action/progress і violet для prediction/evidence states.
- Frontend TypeScript check пройшов. Responsive geometry перевірено у браузері на 320, 375, 768, 1024, 1440 і 1920px без горизонтального document overflow; зміна tuition `12000 → 15000` реактивно оновила investment `36,000 → 45,000 PLN`, keyboard focus видимий, framework overlay і console warnings/errors відсутні. Повний authenticated submit до live backend у цій перевірці не виконувався.

## Implemented but unverified: Phase 7 final visual refinement

- Після responsive QA cost-assumption group переведено у дві колонки на звичайному desktop, щоб прибрати затиснуті labels; три колонки залишаються лише від 1700px. Ця остання CSS-only правка ще не пройшла повторну browser-перевірку.

## Planned: цільова архітектура

- Наявний versioned Simulation Scenario foundation має поступово поєднати education, career, finance, skills, roadmap і evidence.
- Deterministic projection підтримує явний та policy-based вибір validated market snapshots; creation flow, read-only integration і trust presentation реалізовані, а scenario edit/revision UI залишається запланованим.
- Market data storage, deduplication і validation contract реалізовані; fetcher → parser → normalizer та scheduled refresh залишаються запланованими.
- Кожна важлива оцінка повинна мати source, URL/reference, acquisition date, geography, role/seniority, sample size за наявності, confidence/data strength і methodology version.
- Roadmap completion має оновлювати skill evidence та readiness, але не змінювати salary без явної versioned scenario revision.
- RAG слід вводити лише для official university/program/scholarship/curriculum/regulatory documents; PostgreSQL/pgvector оцінюється до окремої vector database.
- Flask/SQLAlchemy modular monolith залишається цільовою backend формою, доки виміряні operational constraints не обґрунтують поділ.

## Відомі розбіжності й обмеження

- Старий опис нижче містить маршрути та user flows, яких немає в поточному Next.js frontend.
- Старі згадки `/api/roi/calculate`, `/pricing`, `/main` і AI salary fallback не відповідають поточній реалізації.
- Roadmap Flask views посилаються на templates, які можуть бути відсутні.
- Frontend plan names не повністю узгоджені з backend entitlement model.
- Browser/runtime стан frontend не підтверджується лише source inspection; перед QA потрібно перевірити checkout, process, URL і port.

---

# Архів попереднього опису — неканонічний

# ROI освіти — опис проєкту

## 1. Ідея та призначення

**ROI освіти** — вебзастосунок для фінансового планування навчання та кар’єри. Його завдання — допомогти користувачу відповісти на практичне питання: чи окупиться обрана освіта, за який час це станеться та як може змінюватися дохід після завершення навчання.

Користувач може:

- вказати університет, спеціальність, вартість навчання, тривалість програми та очікувану стартову зарплату;
- отримати прогноз ROI, термін окупності й сумарний дохід за 5 та 10 років;
- переглянути прогноз зростання зарплати по роках;
- зберігати результати розрахунків у власній історії;
- згенерувати персональний AI-план розвитку до бажаної посади;
- керувати акаунтом і запитувати скидання пароля.

Цільова аудиторія — абітурієнти, студенти, люди, які планують зміну професії, батьки та кар’єрні консультанти.

## 2. Архітектура

Проєкт складається з двох частин:

- **Next.js frontend** у каталозі `frontend/` — основний сучасний інтерфейс із маршрутами App Router;
- **Flask backend** у каталозі `app/` — API, автентифікація, бізнес-логіка ROI, робота з базою даних і інтеграція з DreamWork.

Next.js проксуює запити `/api/*` і `/roadmap/*` до Flask. Авторизація зберігається в HTTP-only cookie `access_token`. Дані користувача та розрахунки зберігаються через SQLAlchemy; міграції виконуються Alembic. У production Flask запускається через Gunicorn, а frontend — через Next.js.

У репозиторії також залишився Flask/Jinja/HTMX-інтерфейс у `app/templates/`. Він містить розширений функціонал калькулятора — autocomplete університетів, історію вартості навчання та повне меню авторизованого користувача. Поточний Next.js UI частину цього функціоналу ще не відображає.

## 3. Користувацький сценарій

1. Користувач відкриває головну сторінку та бачить переваги сервісу.
2. Переходить до калькулятора або спочатку реєструється/входить.
3. Заповнює дані про освіту та натискає розрахунок.
4. Система обчислює фінансові показники, формує прогноз зарплати та зберігає результат для авторизованого користувача.
5. На дашборді користувач переглядає кількість і список останніх розрахунків.
6. За потреби відкриває Roadmap, задає цільову посаду та доступний час на навчання.
7. DreamWork генерує етапи навчального плану, які зберігаються в базі даних і показуються користувачу.

## 4. Маршрути сторінок

| Метод | Маршрут | Призначення | Доступ |
|---|---|---|---|
| GET | `/` | Landing page: опис сервісу, CTA-кнопки та демонстраційні KPI | Публічний |
| GET | `/login` | Форма входу | Публічний |
| GET | `/register` | Форма реєстрації | Публічний |
| GET | `/calculator` | Форма розрахунку ROI та блок результатів | Захищений frontend-маршрут; API потребує авторизації |
| GET | `/main` | Дашборд, кількість і таблиця останніх розрахунків | Авторизований |
| GET | `/roadmap` | Форма AI Roadmap або згенерований навчальний план | Авторизований |
| GET | `/profile` | Налаштування профілю та відновлення пароля | Авторизований у Flask-версії |
| GET | `/trial` | Безкоштовний розрахунок без збереження результату | Публічний |
| GET | `/results` | Повна історія збережених ROI-розрахунків | Авторизований |
| GET | `/pricing` | Опис планів Standard, Pro та Pro + Own Teacher | Публічний |
| GET | `/reset-password` | Запит і завершення скидання пароля | Публічний |

### Навігаційні елементи

- **«ROI освіти»** — повертає на `/`.
- **Кнопка теми ☀/☾** — перемикає світлу/темну тему та зберігає вибір у `localStorage` під ключем `theme`.
- **«Калькулятор»** — відкриває `/calculator`.
- **«Увійти»** — відкриває `/login`.
- **«Реєстрація»** — відкриває `/register`.
- У legacy-меню для авторизованого користувача також є **«Дашборд»** (`/main`), **«Roadmap»** (`/roadmap`), **«Профіль»** (`/profile`) і **«Вийти»**.

## 5. Функціонал і всі кнопки

### Головна сторінка `/`

- **«Розпочати розрахунок»** — перехід до `/calculator`.
- **«Увійти»** — перехід до `/login`.
- Картки «Аналіз вартості навчання», «Прогноз заробітної плати» та «Розрахунок ROI» — інформаційні блоки без окремої дії.
- Демонстраційні значення `$850,000`, `250.5%`, `18 міс.` — статичний preview, а не результат введення поточного користувача.

### Вхід `/login`

Поля:

- електронна пошта;
- пароль.

Кнопки та посилання:

- **«Увійти»** — POST-запит до `/api/auth/login`; після успіху перехід на `/main`.
- **«Зареєструватись»** — перехід до `/register`.
- У legacy-формі кнопка з іконкою ока показує/приховує пароль.
- Legacy-посилання **«Забули пароль?»** наразі має `href="#"` і не веде на окрему сторінку; робочий запит скидання доступний у профілі.

Під час відправлення Next.js показує стан **«Завантаження…»**, а помилка API виводиться у формі.

### Реєстрація `/register`

Поля:

- електронна пошта;
- пароль;
- підтвердження пароля.

Кнопки та посилання:

- **«Зареєструватись»** — POST-запит до `/api/auth/register`, створення користувача, встановлення cookie та перехід на `/main`.
- **«Увійти»** — перехід до `/login`.
- У legacy-версії кнопки з іконкою ока окремо показують/приховують пароль і його підтвердження.

Пароль має містити щонайменше 8 символів, велику й малу літери та цифру. На клієнті додатково перевіряється збіг паролів.

### Калькулятор `/calculator`

Поля форми:

| Поле | Опис |
|---|---|
| Університет | Назва університету або навчального закладу |
| Спеціальність | Наприклад, `Computer Science` |
| Вартість за рік ($) | Річна вартість навчання |
| Тривалість (років) | Кількість років навчання; backend дозволяє від 1 до 12 |
| Очікувана стартова зарплата ($/рік) | Річний дохід після завершення навчання |

Кнопки та елементи:

- **«Розрахувати ROI»** — POST `/api/roi/calculate`, повертає та показує результат без перезавантаження сторінки.
- У legacy-калькуляторі введення університету запускає пошук після мінімум двох символів із debounce приблизно 350 мс.
- У списку університетів можна натиснути **«Обрати»** біля року — вибрана вартість підставляється у поле вартості.
- Autocomplete підтримує клавіші `ArrowDown`, `ArrowUp`, `Enter` і `Escape`, а список закривається при кліку поза ним.
- Legacy-індикатор **«Рахуємо…»** показується під час запиту.

Результат містить:

- ROI у відсотках;
- термін окупності в місяцях;
- прогнозований дохід за 5 років;
- прогнозований дохід за 10 років;
- графік/набір стовпчиків прогнозу зарплати по роках.

### Дашборд `/main`

- Автоматично завантажує `/api/roi/history` після відкриття сторінки.
- Показує кількість збережених розрахунків.
- Посилання **«калькулятор»** у картці статистики веде на `/calculator`.
- Показує статус AI-прогнозу: **«Включено»**.
- Показує картку **«Мій Roadmap»** із позначкою DreamWork.
- Таблиця **«Останні розрахунки»** містить дату, ROI, термін окупності та загальні витрати.
- Якщо історія порожня, показується повідомлення **«У вас ще немає збережених розрахунків»**.

Окремих кнопок редагування чи видалення записів історії наразі немає.

### Roadmap `/roadmap`

Поля:

- **Цільова посада** — наприклад, `Junior Python Developer`;
- **Годин на тиждень** — від 1 до 168, типовий початковий показник — 10.

Кнопки та логіка:

- **«Згенерувати AI Roadmap»** — POST `/roadmap/generate`; відправляє цільову посаду, години, нульовий поточний дохід і порожній список навичок.
- Після успіху форма замінюється планом.
- План може містити заголовок, фази, теми та список завдань.
- При помилці показується повідомлення, а форма залишається доступною для повторної спроби.

У поточному Next.js UI немає кнопки повторної генерації або видалення вже показаного плану. Legacy-версія завантажує останній roadmap користувача на сервері.

### Trial `/trial`

Trial-сторінка викликає `POST /api/roi/trial`. Endpoint не перевіряє cookie, не створює запис у `roi_calculations` і повертає результат лише для поточного запиту. Дані форми додатково тимчасово кладуться у `sessionStorage` браузера під ключем `trial-calculation`. У frontend trial показує базовий результат і заклик зареєструватися; backend технічно повертає повну модель відповіді.

### Результати `/results`, плани `/pricing` і скидання пароля `/reset-password`

- `/results` завантажує `GET /api/roi/history` і показує дату, ROI, окупність, інвестицію та дохід за 10 років. Видалення й редагування не реалізовані.
- `/pricing` є інформаційною сторінкою. Тарифи не підключені до платіжної системи, а обмеження в API зараз фактично не застосовуються: `/api/auth/me` повертає план `Free` та безлімітні значення.
- `/reset-password` має два кроки: generic запит листа через `POST /api/auth/password-reset-request` і зміна пароля через `POST /api/auth/password-reset` з одноразовим opaque Redis-токеном, дійсним 15 хвилин. Токен зберігається лише як SHA-256 keyed reference, атомарно споживається через Redis `GETDEL` і не є JWT.

### Профіль `/profile`

Поточна Next.js-версія містить повний двокроковий flow відновлення пароля:

- email form викликає `POST /api/auth/password-reset-request`;
- лист містить одноразове посилання на `/reset-password#token=...`; fragment не передається frontend-серверу або reverse proxy;
- сторінка одразу прибирає token з address bar після читання;
- форма нового пароля викликає `POST /api/auth/password-reset`;
- expired, replayed і wrong-purpose tokens повертають контрольовану помилку.

Backend навмисно повертає однакове успішне повідомлення незалежно від існування email, щоб не розкривати реєстрацію користувачів.

Якщо SMTP або Celery worker не налаштовані, API навмисно зберігає generic public response; фактична доставка листа потребує робочих SMTP credentials, Redis, broker і Celery worker.

## 6. API-маршрути Flask

### Автентифікація — `/api/auth`

| Метод | Endpoint | Функція |
|---|---|---|
| POST | `/api/auth/register` | Реєстрація, створення access token і cookie |
| POST | `/api/auth/login` | Вхід, створення access token і cookie |
| POST | `/api/auth/logout` | Видалення cookie `access_token` |
| POST | `/api/auth/password-reset-request` | Запит листа для скидання пароля |
| POST | `/api/auth/password-reset` | Зміна пароля за токеном |
| GET | `/api/auth/login/google` | Початок OAuth-авторизації Google |
| GET | `/api/auth/callback/google` | Callback Google OAuth, створення/пошук користувача та redirect на `/main` |
| GET | `/api/auth/me` | Дані поточного користувача, план і лічильники використання |

### ROI — `/api/roi`

| Метод | Endpoint | Функція |
|---|---|---|
| POST | `/api/roi/calculate` | Розрахунок і збереження ROI для авторизованого користувача |
| POST | `/api/roi/trial` | Розрахунок ROI без авторизації та без збереження |
| GET | `/api/roi/history` | Історія розрахунків поточного користувача |
| GET | `/api/roi/universities/search?q=...` | Пошук університетів через зовнішні джерела |
| GET | `/api/roi/universities/tuition?...` | Історія вартості навчання за роками |

Параметри tuition endpoint: `scorecard_id` для університетів США або `country` для середніх даних по країні.

### Roadmap — `/roadmap`

| Метод | Endpoint | Функція |
|---|---|---|
| GET | `/roadmap/` | Отримання сторінки з останнім roadmap у legacy-версії |
| POST | `/roadmap/generate` | Генерація плану через DreamWork і збереження в БД |

## 7. Як рахується ROI

1. Загальна інвестиція в освіту = річна вартість навчання × тривалість навчання.
2. Якщо стартову зарплату не передано, сервіс може отримати оцінку через AI/RAG-сервіс; резервні значення — $45,000 для стартової зарплати та $5,000 для tuition.
3. Прогноз зарплати будується на 10 років за моделлю людського капіталу Мінсера:
   - 1–3 роки досвіду: приблизно +8% на рік;
   - 4–6 роки: приблизно +5%;
   - 7–10 роки: приблизно +3%;
   - далі: плато приблизно +2%.
4. ROI = `(сумарний дохід за 10 років − витрати на освіту) / витрати на освіту × 100`.
5. Термін окупності — кількість місяців, за які накопичений дохід після навчання покриває інвестицію.

Розрахунок є прогнозом, а не гарантією працевлаштування чи майбутнього доходу. Поточна модель не враховує податки, інфляцію, вартість життя, кредити, альтернативну вартість часу, безробіття та ризик зміни професії.

## 8. Редіректи та проходження запиту

### Frontend middleware

`frontend/middleware.js` працює до рендерингу Next.js-сторінки:

- якщо немає cookie `access_token` і відкрито `/main`, `/calculator`, `/results`, `/profile` або `/roadmap`, виконується redirect на `/login?next=<початковий-маршрут>`;
- якщо cookie є, а користувач відкриває `/`, `/login` або `/register`, виконується redirect на `/main`;
- `/trial`, `/pricing` і `/reset-password` middleware не захищає.

`next` використовується компонентом `AuthForm` після успішного входу або реєстрації. Дозволяються лише внутрішні шляхи, що починаються з одного `/`; значення на кшталт `//external-site` відкидаються, після чого використовується `/main`.

### Next.js rewrites/proxy

`frontend/next.config.mjs` проксуює:

- `/api/:path*` → `${FLASK_API_URL}/api/:path*`;
- `/roadmap/:path*` → `${FLASK_API_URL}/roadmap/:path*`.

Для браузера це same-origin запити до Next.js, тому cookie надсилається разом із запитом до proxy, а Flask читає її як звичайний `access_token`. У Docker `FLASK_API_URL=http://api:8122`; локально типовим значенням є `http://localhost:8122`.

### Backend auth decorator

`get_current_user` використовує `g.user`, якого Flask заповнює у `before_request`: JWT декодується, з нього береться `sub` з ID користувача, після чого перевіряються активний статус і наявність користувача в БД.

- Для `/api/*` і HTMX-запитів без валідної сесії повертається HTTP `401` у JSON/HTML-форматі.
- Для звичайних захищених Flask/Jinja сторінок виконується HTTP `302` redirect на `/login`.
- Для авторизованого користувача endpoint продовжує виконання і передає `user` у view-функцію.

### Auth redirects

- JSON login/register встановлюють HTTP-only cookie та повертають JSON; frontend після цього робить `router.replace(next || "/main")`.
- HTMX login/register замість JSON повертають заголовок `HX-Redirect: /main` і також встановлюють cookie.
- Google flow: `/api/auth/login/google` перенаправляє на Google; Google повертає користувача на `/api/auth/callback/google`; callback створює або знаходить користувача, встановлює cookie й робить redirect на `${FRONTEND_URL}/main`.
- Logout видаляє cookie `access_token` і повертає JSON. Frontend dashboard після logout перенаправляє браузер на `/`.

Важливий поточний стан: `setup_oauth(app)` визначений у `app/core/oauth.py`, але його виклик у `create_app()` зараз вимкнений/відсутній. Тому Google OAuth потребує окремого підключення ініціалізації перед використанням; самих маршрутів і змінних `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` недостатньо.

## 9. Обробка помилок і безпека

- Захищені endpoints перевіряють access token із cookie.
- Паролі проходять серверну валідацію та не передаються у відкритих URL.
- Помилки валідації повертаються як зрозуміле повідомлення для форми.
- Після завершення сесії користувача legacy-інтерфейс переводить на `/login`.
- Password reset не дозволяє визначити, чи існує конкретна електронна адреса.
- Помилка інтеграції DreamWork повертається як повідомлення про недоступність зовнішнього сервісу.

## 10. Сервіси та інтеграції

### База даних і міграції

Основне сховище — PostgreSQL. Моделі SQLAlchemy: `User`, `University`, `EducationProgram`, `ROICalculation`, `UserRoadmap`, `SalaryStatistic` і `CareerForecast`. Розрахунки та roadmap прив’язані до `user_id`; при видаленні користувача пов’язані записи видаляються каскадно. Структура БД версіонується Alembic, тому після запуску PostgreSQL потрібно виконати `alembic upgrade head`.

### AI/RAG і Chroma

Якщо `expected_start_salary` не передано, `ROIService` створює `AIRAGService`, шукає релевантний контекст у локальному Chroma vector store і просить Ollama повернути прогноз зарплати та кар’єрні показники у JSON. Дані зберігаються у `CHROMA_PERSIST_DIR` (типово `./chroma_db`). Якщо Ollama, LLM або Chroma недоступні, застосовуються резервні значення: стартова зарплата `$45,000`, середня зарплата `$60,000`, ріст `3%`, demand score `70`, AI risk score `30`. Коли зарплата передана у формі, AI/RAG для цього розрахунку не викликається.

### DreamWork

`POST /roadmap/generate` виконує послідовність:

1. авторизується у DreamWork через `/api/auth/login` із `DREAMWORK_USERNAME` і `DREAMWORK_PASSWORD`;
2. створює симуляцію через `/api/simulation/simulate`;
3. генерує план через `/api/plan/generate`;
4. зберігає відповідь у `user_roadmaps` і повертає її frontend.

Клієнт має таймаути HTTP-запитів і перетворює помилки зовнішнього сервісу на HTTP `502`. Access token DreamWork кешується лише в межах одного екземпляра `DreamworkClient`; кожен виклик генерації створює новий клієнт. Усі користувачі наразі використовують один service account.

### Університети та tuition

Пошук паралельно використовує College Scorecard для США та Hipolabs для світових результатів; американські результати показуються першими й можуть містити `scorecard_id`. Історія tuition для США береться за 2018–2023 роки з College Scorecard, для інших країн — із вбудованого словника `NON_US_TUITION` (наразі фактичні дані є, зокрема, для України). Зовнішні HTTP-виклики мають timeout 8 секунд; при помилці endpoint повертає порожній список.

### Celery, RabbitMQ і email

Запит скидання пароля не відправляє email синхронно: для існуючого активного користувача ставиться Celery-задача `send_verification_email.delay(email, token)`. RabbitMQ є broker, типовий result backend — `rpc://`, а worker запускається командою `celery -A app.core.celery_app worker --loglevel=info`. Без `SMTP_PASSWORD` лист не надсилається назовні, а токен лише записується в лог як `[MOCK EMAIL]`; при помилці SMTP задача повторюється до 3 разів із затримкою 60 секунд.

## 11. Конфігурація та запуск

Основні змінні середовища:

| Змінна | Призначення | Типове/приклад |
|---|---|---|
| `DATABASE_URL` | Підключення SQLAlchemy/Alembic до PostgreSQL | `postgresql://...` |
| `SECRET_KEY` | Секрет підпису JWT і Flask | обов’язково змінити в production |
| `ALGORITHM` | Алгоритм JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Тривалість access token | `30` |
| `FLASK_API_URL` | Адреса Flask для Next.js proxy | `http://localhost:8122` локально, `http://api:8122` у Docker |
| `FRONTEND_URL` | Адреса frontend для OAuth callback redirect | `http://localhost:3221` |
| `PASSWORD_RESET_URL` | Необов'язкова точна адреса frontend reset page у листі | `${FRONTEND_URL}/reset-password` |
| `OAUTH_REDIRECT_URI` | Callback URI, зареєстрований у Google | `http://localhost:3221/api/auth/callback/google` |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth credentials | не задані за замовчуванням |
| `DREAMWORK_API_URL`, `DREAMWORK_USERNAME`, `DREAMWORK_PASSWORD` | Підключення до DreamWork | див. `.env` |
| `COLLEGE_SCORECARD_API_KEY` | College Scorecard API key | `DEMO_KEY` |
| `CHROMA_PERSIST_DIR` | Каталог vector store | `./chroma_db` |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Черга та backend Celery | RabbitMQ / `rpc://` |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_HOST`, `SMTP_PORT` | Відправлення reset email | Gmail SMTP, порт `587` |
| `LOG_LEVEL`, `LOG_FILE` | Рівень і файл логування | `INFO`, `app/logs/app.log` |

Docker Compose піднімає frontend на `3221`, Flask API на `8122`, PostgreSQL на host-порті `5442`, RabbitMQ на `5672`, а RabbitMQ Management UI — на `15672`. Після старту контейнерів застосовуються міграції командою `docker compose exec api alembic upgrade head`. Для локального frontend потрібно виконати `cd frontend`, `npm install`, `npm run dev`.

## 12. Поточні обмеження та напрямки розвитку

- Next.js Header для публічних сторінок показує базові посилання; повна навігація Roadmap/Profile і logout доступні в dashboard layout, а не в публічному Header.
- У legacy login кнопка «Забули пароль?» ще є заглушкою `#`; у Next.js UI робочий сценарій доступний на `/reset-password`.
- Frontend-калькулятор уже підтримує autocomplete університетів і вибір tuition по роках; окремі UI-тести для цих сценаріїв ще відсутні.
- Усі roadmap генеруються через один глобальний сервісний акаунт DreamWork; майбутній варіант — персональний OAuth/SSO-зв’язок для кожного користувача.
- Потрібні окремі тести UI, уніфікована обробка станів завантаження/помилок у всіх запитах, редагування roadmap та деталізовані графіки.
- Для production бажано ввімкнути secure cookies, HTTPS, rate limiting, CSRF-захист і централізований моніторинг помилок.
