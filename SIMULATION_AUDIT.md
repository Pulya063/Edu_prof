# Аудит створення симуляції та фінансового аналізу

Дата: 2026-10-07. Checkout: `C:\Users\Pulya\PycharmProjects\Egzamin_success`.

## Current: потік даних

1. `ScenarioBuilder.tsx` перевіряє stored tuition через `/api/tuition/snapshots/resolve`. За відсутності джерела користувач явно вводить ціну.
2. `POST /api/simulations` валідує `SimulationCreateRequest`, перевіряє відповідність tuition і зберігає `SimulationScenario` та першу `SimulationRevision`.
3. Окремий POST projections вибирає salary snapshot або manual salary з evidence. `SimulationProjectionService` перевіряє власника, країну, валюту та обов'язкові джерела.
4. `DeterministicProjectionEngine` рахує direct/opportunity costs, різницю доходів проти baseline, окупність і ROI. Зовнішні API та LLM у цьому розрахунку не викликаються.
5. `SimulationProjection` зберігає входи, результат, методологію, fingerprint і evidence. Overview та scenario details читають ці записи.

Створення сценарію й прогнозу — дві транзакції: невдалий прогноз залишає сценарій доступним. UI має partial-success стан. Landing simulation залишається локальною демонстрацією, а roadmap — окремим потоком.

## Current: видалено

| Маршрут або код | Підстава |
|---|---|
| `POST /api/roi/analyze` | Лише retired 410-відповідь; немає викликів у застосунку. Тепер 404. |
| `GET /api/roi/trash` | Немає споживачів чи запланованого legacy trash UI. Тепер 404. |
| `DELETE /api/roi/<id>` | Немає споживачів; фізичне видалення не узгоджувалось із restore. Тепер 404. |
| `POST /api/roi/<id>/restore` | Немає споживачів; старий delete не залишав запису для відновлення. Тепер 404. |
| `ROIService.analyze_career`, `_save_career_analysis` | Старий writer не викликався жодним чинним маршрутом; суперечив переходу на projections. |
| `_generate_qualitative_insights`, `_money`, `_range`, `_mincer_rate`, старі константи та імпорти | Залежали від видаленого writer або взагалі не викликалися. |
| `get_history`, `serialize_history`, `CareerAnalysisRequest`, `ROICalculationResponse` | Зайвий шлях серіалізації та контракти видаленого коду. |

Перевірено посилання в backend, frontend, тестах і документації репозиторію. Наявність зовнішніх клієнтів поза репозиторієм не перевірена.

## Current / Planned: збережено

- Усі simulation endpoints: створення, список, деталі, overview, revisions, projections та explainability. Revision UI є **Planned**; його backend уже **Current**.
- Market/tuition ingestion, читання і resolver: потрібні для джерел прогнозу, навіть коли немає кнопки для кожного endpoint.
- `/api/roi/trial`: окремий чинний чотирипольовий public contract і diagnostic consumer; не є новим фінансовим звітом workspace.
- `/api/roi/history`: доступ до історичних записів власника. Legacy university search/tuition читаються старим JavaScript.
- Legacy ORM-моделі, поля та міграції: потрібні для історичних даних і зв'язків. Таблиці й користувацькі дані не видалялися.
- AI/RAG та O*NET модулі не видалені глобально: аудит очищає старий writer, а не всю інтеграційну інфраструктуру.

## Виявлені обмеження, які залишаються

- Manual evidence перевіряється за metric, country і currency; правдивість джерела, відповідність role/seniority і давність не підтверджуються. Це не незалежно перевірена статистика.
- Прямий tuition snapshot ID перевіряє country/currency/university/program, але не всі умови degree/residency. Policy resolver має ширший набір критеріїв.
- Послідовний повтор прогнозу дедуплікується. Два одночасні запити можуть пройти initial SELECT і зіткнутися з unique constraint при commit; спеціального retry немає. Конкурентний PostgreSQL-тест не виконувався.
- Overview обирає сценарій за `updated_at`, без фільтра `status`; зараз API не має операції архівування, але перед її додаванням слід узгодити поведінку.
- Legacy trial використовує спрощену окрему методологію та типову країну США. Не слід порівнювати його числа з versioned projection як еквівалентні.

## Перевірка

**Verified:** `.venv\Scripts\python.exe -m pytest tests -q --basetemp=.pytest-audit-tmp` — **40 passed** (2026-10-07). Перевірені чинний scenario/projection flow, snapshot resolution, відсутність видалених маршрутів, owner-scoped legacy history та приховування раніше видалених записів. Перший запуск виявив помилку назви поля в новому тесті; її виправлено перед повним успішним запуском.

Live PostgreSQL, browser QA і зовнішні provider requests не входили в перевірку очищення backend. Схема БД не змінена; нової міграції не потрібно.
