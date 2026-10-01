# Execution — Shubham Kumar's development playbook

Status: PLANNED. Replaces Team.md: there is exactly one developer and committer. AI tools assist; **the human decides, reviews every diff, and owns every commit.**

## 1. Responsibilities (all held by Shubham Kumar)

Product decisions · architecture · AI/ML · frontend · backend · database · integration · GitHub · testing · deployment · demo. AI agents are assistants for implementation, review and drafting only; they never own a decision.

## 2. The loop (every task)

```
READ DOCS → UNDERSTAND TASK → INSPECT CODE → PLAN → IMPLEMENT → TEST → DIFF REVIEW → COMMIT → UPDATE MEMORY
```

| Step | What you do | What the agent does | Output |
|---|---|---|---|
| READ DOCS | Name the docs and sections for the task (Phases.md phase → linked docs) | Reads `AGENTS.md`, `Memory.md`, the named sections | Agent restates the task in its own words |
| UNDERSTAND | Confirm restatement; answer questions | Lists assumptions and doc contradictions | Agreed scope |
| INSPECT CODE | — | Lists relevant existing files, reads them | File list + findings |
| PLAN | Approve/modify | Writes plan: files to change, functions, tests, risks (Rules AI-2) | Approved plan |
| IMPLEMENT | Watch for plan deviations | Smallest change that satisfies plan | Code |
| TEST | Run or watch the real commands | Runs tests/linters/build; pastes real output | Evidence |
| DIFF REVIEW | Read `git diff` fully | Summarises diff vs plan | Clean diff or fixes |
| COMMIT | `git add -p`, Conventional Commit | Drafts message | Commit |
| UPDATE MEMORY | Edit Memory.md (§8) | Proposes the edit | Memory current |

## 3. Daily workflow

| Block | Activity |
|---|---|
| Start (10 min) | `git status`; read Memory.md "Next action"; pick the next phase task; confirm the day's checkpoint from Phases.md §16 |
| Work cycles (90 min) | One task per loop (§2); keep tasks to ≤ 90 min; commit at the end of each |
| Checkpoint (every 3–4 h) | Run full backend tests + frontend build; run the demo path steps built so far; update Memory.md |
| Overrun check | If a phase is at 1.5× estimate → stop, apply the cut list (Phases.md §15), log the decision |
| End of day (20 min) | All tests green on `main`; tag `phase-NN-done` if complete; write Memory.md "Next action" precisely; push to GitHub remote (backup) |

Sleep and breaks are part of the plan; Day 3 afternoon is verification, not features.

## 4. Coding workflow rules of thumb

Backend first for each module (schema → service → tests → router), then frontend page against the real endpoint. Pure functions before DB-dependent code. Write the acceptance-criteria test before or with the code. Never leave the app broken between commits.

## 5. Git workflow

| Item | Rule |
|---|---|
| Remote | One private/public GitHub repo; push at least at each phase end |
| Main | `main` is always runnable |
| Branches | **One short-lived branch per phase**: `phase/NN-name` (e.g., `phase/05-forecasting`). Created from `main`; merged to `main` (fast-forward or squash) when exit criteria pass. Optional: `fix/<topic>` for urgent bugs. No long-lived branches, no parallel branches (single developer) |
| Why branch at all | Safety net against a bad agent run; easy `git reset` to the last good state |
| Tags | `phase-NN-done` at each exit; `demo-ready` at freeze |
| Commit style | Conventional Commits: `feat(matching): …`, `fix(orders): …`, `docs(api): …`, `test(routes): …`, `chore: …`; one logical change each |
| PRs | Not required. Optional self-PR to review a large diff in GitHub's UI; CI is NICE |
| Before commit | `ruff check`, `pytest -q`, `npm run build` (and `npm run test` if frontend logic changed), review `git diff --staged` |
| Never commit | `.env`, `app.db`, `node_modules`, `.venv`, raw datasets of unclear licence |
| Recovery | `git stash` / `git restore` / `git reset --hard <tag>`; never force-push shared history without need |

## 6. AI-agent workflow

**Context pack for every task:** `AGENTS.md` + `Memory.md` + the exact doc sections named in Phases.md for the phase + the file list. Do not paste the entire doc set each time.

**Task prompt template**
```
TASK: <one sentence, from Phases.md deliverables>
READ FIRST: AGENTS.md, Memory.md, docs/<files + sections>
SCOPE: modify only <files>. Do not add dependencies (Architecture §19).
CONTRACT: follow docs/API.md <endpoints> and docs/Data.md <tables> exactly. Do not invent fields.
PLAN FIRST: list files, functions, tests; wait for my "go".
DONE WHEN: <acceptance IDs from Testing.md> pass; paste real command output.
REPORT: summary, git diff stat, anything outside the plan, doc updates needed.
```

**Stop-and-ask conditions:** ambiguity, doc contradiction, test you can't explain, wish to change schema/API/scope, need for an unlisted dependency or external service (Rules AI-13).

**Agent hygiene:** one agent session = one task; start a fresh session when context drifts; ask the agent to re-read the doc section instead of trusting memory; reject "tests should pass" statements without output.

## 7. Tool roles

| Tool | Use for | Avoid |
|---|---|---|
| **Antigravity** (agentic IDE; verify current features yourself — this playbook is tool-agnostic) | Main implementation loop: give the context pack and task prompt, require a plan before edits, review its diffs and test output | Letting it refactor outside scope; accepting multi-file rewrites without a plan |
| **Claude (chat)** | Architecture questions, reviewing a doc contradiction, drafting tests/acceptance cases, debugging reasoning, updating docs, rehearsing the Q&A | Pasting secrets; treating answers as verified facts about library APIs |
| **Claude Code** (terminal) | Repo-wide inspection, running tests, focused multi-file edits | Open-ended "improve the project" prompts |
| **Cursor / Copilot** | Inline completion, small edits, writing boilerplate (schemas, components) | Architectural decisions |
Pick one primary agent per task; do not run two agents editing the same files.

## 8. When to update Memory.md

After each task if state changed; always: end of each phase, after any decision, after any scope cut, after discovering a bug, before ending a day, and after any doc correction. Format: update the relevant section in place and append a dated line to the decision/change log. Never record unexecuted results.

## 9. Moving from documentation to implementation

1. Create the repo and copy the docs exactly as in README.md structure; commit `docs: initial documentation package`.
2. Read Phases.md §2 (Phase 0) and run the **first Antigravity task** (§10).
3. Proceed phase by phase; each phase starts by re-reading its Phases.md entry and the linked doc sections.
4. If implementation reality contradicts a doc, fix the doc first (Rules AI-6), log it in Memory.md, then code.
5. At Phase 12 run the Testing.md release gate and the Demo.md checklist.

## 10. First Antigravity task (Phase 0)

```
TASK: Phase 0 — scaffold the KrishiSetu repository exactly per docs/Architecture.md §3.
READ FIRST: AGENTS.md, Memory.md, docs/Architecture.md (§1–§3, §15–§19), docs/Phases.md (Phase 0), docs/Rules.md.
PLAN FIRST: list every file/folder you will create and every command you will run; wait for "go".
DO:
1. Create backend/ (FastAPI app factory in app/main.py, GET /api/v1/health returning {status, db, model, demo_mode, version}; app/core/config.py using pydantic-settings; empty module folders with __init__.py; requirements.txt with ONLY the backend dependencies in Architecture §19; .env.example with the variables in Architecture §17).
2. Create frontend/ (Vite + React + TypeScript + Tailwind; a single page that calls /api/v1/health through the Vite proxy and shows the result; .env.example).
3. Add .gitignore (.env, *.db, node_modules, .venv, __pycache__, dist), root README.md placeholder, and keep docs/ and Memory.md as provided.
4. Add backend/tests/api/test_health.py.
DO NOT: add features, models, other dependencies, or change docs (report conflicts instead).
DONE WHEN (paste real output): pip install succeeds and `python -c "import ortools, lightgbm"` works; `pytest -q` passes; `uvicorn app.main:app` serves /api/v1/health; `npm run build` succeeds; both dev servers start and the page shows the health result.
REPORT: versions installed (for pinning), git diff stat, any doc conflicts.
```

## 11. AGENTS.md (create at repo root in Phase 0)

```
# AGENTS.md — read before any task
Project: KrishiSetu (SIH26033). One developer: Shubham Kumar. You are an assistant.
Read order: Memory.md → docs/Rules.md → the doc sections named in the task.
Authoritative docs: docs/Architecture.md, Data.md, ML.md, API.md, Design.md, Testing.md, Phases.md.
Always: inspect before editing; plan before major changes; smallest diff; no new dependencies; no invented APIs/fields/data/results;
update docs in the same change if behaviour/schema/API changes; run tests and paste real output; review git diff.
Never: claim unimplemented features; fake metrics; add payments/chat/social/microservices; present synthetic data as real.
Stop and ask when: requirements conflict, a doc is ambiguous, a test fails unexplained, scope/schema/API would change.
```

## 12. Personal safety nets

Timeboxes per phase; cut list; nightly push; `demo-ready` freeze at T−4h; recorded demo video made on Day 3 evening as insurance.
