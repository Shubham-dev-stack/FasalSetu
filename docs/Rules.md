# Rules — KrishiSetu

These rules bind the developer (Shubham Kumar) and every AI coding agent (Antigravity, Claude Code, Cursor, Copilot, others). If a rule conflicts with a convenient shortcut, the rule wins. If a rule is wrong, change it here first and record the change in Memory.md.

Precedence when documents disagree: **Rules.md > Architecture.md > Data.md > ML.md > API.md > Design.md > Phases.md > PRD.md > others.** Conflicts are fixed in the lower document and logged in Memory.md.

## 1. Code rules

| # | Rule |
|---|---|
| C-1 | One developer owns the codebase. No other person commits. |
| C-2 | `main` must always run. Work happens on a short-lived `phase/NN-name` branch; merge only after tests pass (Execution.md §5). |
| C-3 | Keep commits focused: one logical change, Conventional Commit message. |
| C-4 | Keep modules focused; respect the dependency rules in Architecture.md §4. |
| C-5 | No unrelated refactoring. If a refactor is needed, make it a separate commit with its own justification. |
| C-6 | Preserve working behaviour; if a test passed before your change it must pass after. |
| C-7 | **Do not invent APIs.** Endpoints, fields and enums come from API.md and Data.md. Missing? Update the doc first. |
| C-8 | **Do not invent datasets.** Only datasets in Data.md §2. |
| C-9 | **Do not invent results.** Metrics, timings, savings and pass/fail statuses come from executed commands only. |
| C-10 | **Do not claim unimplemented features** in UI text, README, demo script or chat. Status words: PLANNED / MVP / FUTURE. |
| C-11 | No dependency may be added unless listed in Architecture.md §19 (update that section first). |
| C-12 | No secrets in the repo; `.env` is git-ignored; `.env.example` has placeholders only. |
| C-13 | All "today" logic goes through `core/dates.today_ist()`. No `date.today()` elsewhere. |
| C-14 | All distances/costs go through `core/geo.py` and `logistics/cost.py`; no duplicate formulas. |
| C-15 | Constants that are assumptions live in `backend/config/*.yaml`, never hard-coded. |

## 2. AI coding rules

| # | Rule |
|---|---|
| AI-1 | **Inspect before editing:** list the relevant files, read them, read the relevant doc sections. |
| AI-2 | **Explain the approach before any major change** (more than ~3 files, any new module, any schema change) and wait for the developer's go-ahead. |
| AI-3 | Modify only the files required for the task. State the file list in the plan. |
| AI-4 | Read `AGENTS.md`, `Memory.md` and the docs named in the task before writing code. |
| AI-5 | Never rewrite the project or large files blindly; prefer targeted edits. |
| AI-6 | **Never change architecture, schema, API contracts or scope without updating the documentation in the same change** and adding a Memory.md entry. |
| AI-7 | **Test before declaring completion.** Run the commands in the task's acceptance list and paste the real output. Never write "tests pass" without running them. |
| AI-8 | Review `git diff` before proposing a commit; report anything outside the plan. |
| AI-9 | If the task cannot be completed as specified, stop and report — do not silently substitute a different design. |
| AI-10 | Do not fabricate library APIs: check the installed version's docs/source (especially OR-Tools and LightGBM) before using a function you are not certain exists. |
| AI-11 | Do not delete or weaken tests to make them pass. |
| AI-12 | Do not add features "while you are there". |
| AI-13 | Stop conditions (ask the developer): ambiguous requirement, a doc contradiction, a failing test you cannot explain, any need for network access to an unlisted service. |

## 3. Data rules

| # | Rule |
|---|---|
| D-1 | Every record is real (with provenance) or synthetic/demo (flagged). Never mix silently. |
| D-2 | Preserve provenance fields (`source`, `is_synthetic`, `is_demo`, `generator_version`). |
| D-3 | **No fake statistics.** No number appears in docs, UI or pitch unless computed by the system or cited from a source in Research.md §12. |
| D-4 | **No fake model accuracy.** Model metrics come only from `model_card.json` produced by `ml.train`, and are always labelled "on synthetic data". |
| D-5 | **No fake real-time claims.** Nothing is "live". Price data is a dated snapshot or synthetic. |
| D-6 | Synthetic data is always identifiable in the DB, API response (`data_source`) and UI badge. |
| D-7 | Demo seed is deterministic; tests rely on it. Changing it requires updating Data.md §12 and Demo.md. |
| D-8 | Do not commit raw downloaded government data if its licence is unclear; commit only derived, labelled samples. |

## 4. Product rules

| # | Rule |
|---|---|
| P-1 | Stay inside SIH26033. Every feature maps to an SIH-1…7 code in PRD.md. |
| P-2 | Do not become a generic e-commerce app: no cart, reviews, coupons, wishlists, recommendations-for-you. |
| P-3 | No social features, chat, notifications infrastructure. |
| P-4 | No payment system (D-006). The UI says settlement happens outside the platform. |
| P-5 | No fake live logistics. Shipment status is manual and labelled as such. |
| P-6 | No fake farmer-income claims. Price comparisons are **modelled scenarios** with visible assumptions. |
| P-7 | No fake GPS tracking or vehicle positions. Routes are planned, not tracked. |
| P-8 | No unnecessary AI: matching, pricing and logistics stay deterministic. No LLM features. |
| P-9 | No blockchain, microservices, queues, websockets. |
| P-10 | Individual household consumers are out of scope (D-005). |

## 5. Claims register (what may be said)

| Topic | Allowed | Not allowed |
|---|---|---|
| Forecast quality | "On synthetic data, LightGBM achieved MAE X vs baseline Y (model card)" — after it is measured | "95% accurate", "production-grade forecasts" |
| Savings | "Modelled scenario: direct landed price is X% below the traditional-chain scenario under these assumptions" | "Farmers earn X% more", "consumers save X%" |
| Route optimization | "Optimized plan uses N km vs M km for the modelled unconsolidated baseline" | "Reduces fuel cost by X% in practice" |
| Uniqueness | "Integrates forecast, matching, routing and price transparency in one flow" | "First/only platform", "no one does this" |
| Data | "Synthetic demo data; Agmarknet snapshot dated D (if ingested)" | "Real-time mandi prices" |
| Scale | "Demo region: Delhi-NCR belt, 5 crops" | "Nationwide platform" |
| Competitors | Factual, sourced statements (Research.md §3) | Disparagement, unverified claims |

## 6. Testing rules

Never state a test passed unless it was executed in the current session with output shown. Failing tests are reported as failing. Skipped tests are listed as skipped. The execution log in Testing.md §15 is append-only.

## 7. Documentation rules

Docs are part of the codebase. A change to behaviour, schema, API, config defaults or scope updates the matching doc in the same commit. Memory.md is updated at the end of each phase and after any decision (Execution.md §8).

## 8. Anti-overengineering rules

If a task seems to need a queue, cache server, new service, new framework, new ML family or a new external API — stop. The answer is almost always a simpler function, a config value, or cutting the feature (see cut list, Phases.md §15).
