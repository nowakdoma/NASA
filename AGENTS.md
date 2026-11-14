# FieldShift — instructions for all coding agents and humans

> `CLAUDE.md` and `GEMINI.md` are symlinks to this file. Edit only `AGENTS.md`.

## Goal

FieldShift is a decision-support tool for the NASA Space Apps 2026 challenge
"Field Shift: Adapting Farms with NASA Data". For **Finney County, Kansas** (FIPS 20055)
it shows:

- a map of irrigated fields coloured by crop (USDA CDL history 2008–2025) with a year slider;
- a per-field "passport": crop history, bare-soil periods, water/heat stress windows, soil;
- five farmer priority sliders: water, income, soil organic matter, erosion, labour;
- a comparison of 4 rotation strategies (current + 3 alternatives) with p10/p50/p90 intervals
  from the 1995–2025 weather distribution, a "P(best)" under uncertain priorities, and a
  "what we don't know / verify locally" box.

**Results are decision support with uncertainty, never recommendations.** The tool supports,
not replaces, farmer judgment. In code, UI copy, docs and the pitch: say "under these
priorities, strategy X scores highest in N % of weather/weight samples", never "you should
plant X". Always show intervals and data gaps next to point values.

All computation is offline. The web app reads only static JSON/GeoJSON from `web/public/data/`.

## Layout and ownership

| Path          | Owner                          | What lives there                                                                 |
| ------------- | ------------------------------ | -------------------------------------------------------------------------------- |
| `contracts/`  | **shared — human approval**    | JSON Schemas, `crops.csv`, realistic mocks. The integration point.               |
| `engine/`     | person 3 (from 2026-11-14)     | FAO-56 water balance, simplified RUSLE, soil-conditioning index, MCDA, export    |
| `pipeline/`   | person 2                       | Download + harmonise NASA POWER, MODIS NDVI, SMAP, SRTM, CDL, SSURGO             |
| `web/`        | person 1 (UI/UX, pitch, slides) | Vite + React + TS, MapLibre GL + deck.gl, Recharts                              |
| `notebooks/`  | anyone                         | Exploration only, small cells (`# %%` percent format). Nothing imports from here |
| `data/`       | pipeline writes                | gitignored raw + interim. Only small processed outputs go to `web/public/data/`  |
| root files    | person 1                       | `AGENTS.md`, `TASKS.md`, `Makefile`, `pyproject.toml`                            |

Rules:

1. **An agent edits only its owner's directory.** If you need a change elsewhere, write it
   in `TASKS.md` under "Blockers / requests" and tell your human.
2. **`contracts/` changes only with explicit human approval** from all three people. Bump
   `schema_version` and update schema + mock + `web/src/types/contracts.ts` in the same commit.
3. Data flow: `pipeline/` → `data/interim/*` → `engine/` → `python -m engine.export` →
   `web/public/data/*.json` (must validate against `contracts/`).

## Commands

```bash
make setup    # uv sync + pnpm install + pre-commit install
make data     # run pipeline (stubs for now; downloads need .env Earthdata creds)
make export   # engine → web/public/data (currently copies contracts/mock)
make dev      # Vite dev server on http://localhost:5173
make check    # ruff, pytest, contract validation, prettier, tsc, web build — must pass
```

Python: `uv run python -m engine.validate`, `uv run pytest`, `uv run python -m pipeline --help`.
Web: `cd web && pnpm dev | pnpm build | pnpm typecheck | pnpm format`.

## Working rules

- **Run `make check` before every commit.** Do not commit with a failing check.
- **Small, frequent commits** with clear messages (`engine: add Kc curve`, `web: field panel`).
- **`git pull --rebase` before `git push`.** Never force-push `main`.
- **Do not mass-reformat or refactor.** Format only the files you changed. No renames or moves
  of other people's code. No drive-by "cleanups".
- **Secrets only in `.env`** (gitignored; template in `.env.example`). Never print, log or
  commit credentials.
- **No new dependencies without asking the humans.** Current allow-list is in
  `pyproject.toml` and `web/package.json`.
- **No deep learning.** Modelling is statistical/process-based. LightGBM + conformal
  intervals are a later optional step, only if time allows.
- Do not download large data into the repo; `data/` is gitignored.
- Mark placeholder or uncertain numbers explicitly (`placeholder=true`, `"mock": true`, or a
  `data_gaps` entry). Never present a placeholder as a measured value.
- Environment: WSL2 Ubuntu, LF line endings (`.gitattributes`), Python 3.11 via uv, Node 22
  + pnpm 9 (corepack). Keep the repo inside the Linux filesystem (`~/...`), not `/mnt/c`.
  On WSL1 the Makefile sets `UV_LINK_MODE=copy UV_CONCURRENT_INSTALLS=1` (uv otherwise fails
  with ENOMEM) and numpy prints a harmless `longdouble` warning.

## Timeline (Space Apps 2026 weekend)

- **Sat 20:00** — real data ready in contract format
- **Sun 08:00** — MVP frozen (only bug fixes + pitch after this)
- **Sun 12:30** — submission (hard deadline 13:30)

# UX Design Instructions

Follow these instructions whenever you design, build, or revise a user interface. Apply them across layouts, navigation, onboarding, forms, settings, dashboards, and interactive flows.

Your goal is to minimize confusion, reduce effort, prevent mistakes, and help users complete their intended task as quickly as possible.

## 1. Reduce Choices per Screen: Hick's Law

The time required to make a decision increases with the number and complexity of available choices.

* Give each screen one clear purpose.
* Remove irrelevant or low-priority options.
* Break complicated decisions into smaller steps.
* Recommend an option when users may struggle to choose.

## 2. Make Targets Large: Fitts's Law

Large, nearby targets are faster and easier to interact with.

* Make buttons and controls easy to click or tap.
* Give interactive elements sufficient spacing.
* Avoid tiny icons as the only interaction target.
* Increase the clickable area around important controls.

## 3. Follow Familiar Patterns: Jakob's Law

Users expect your product to work like products they already understand.

* Use established interface conventions.
* Place navigation, search, settings, and account controls where users expect them.
* Use familiar icons and interaction patterns.
* Do not invent a new pattern unless it provides a meaningful advantage.

## 4. Group Related Information: Law of Proximity

Elements positioned near one another are perceived as related.

* Place related labels, controls, and information together.
* Use spacing to communicate relationships.
* Separate unrelated groups with additional space.
* Do not rely on borders when spacing can establish the hierarchy.

## 5. Break Content Into Chunks: Miller's Law

Working memory can only process a limited amount of information at once.

* Divide long content into small, meaningful groups.
* Break complex forms and tasks into manageable steps.
* Use headings, sections, and concise labels.
* Avoid asking users to remember information between screens.

## 6. Respond Within 400 Milliseconds: Doherty Threshold

Interfaces feel more productive when feedback appears within approximately 400 milliseconds.

* Acknowledge every user action immediately.
* Show loading, processing, or success states when results are not instant.
* Use optimistic updates when they are safe.
* Never leave users wondering whether their action registered.

## 7. Highlight the Primary Action: Von Restorff Effect

An element that visually differs from surrounding elements receives more attention.

* Give the primary action the strongest visual emphasis.
* Use one dominant call to action per section.
* Keep secondary actions visually quieter.
* Avoid making every button compete for attention.

## 8. Place Key Actions Nearby: Fitts's Law

Interaction becomes faster when important targets are close to the user's current focus.

* Place actions beside the content they affect.
* Keep form submission near the final input.
* Position frequent actions within easy reach.
* Avoid forcing unnecessary cursor or eye movement.

## 9. Put Essentials First: Serial Position Effect

People remember the first and last items in a sequence most clearly.

* Put the most important information first.
* Place the final action or takeaway at the end.
* Keep lower-priority information in the middle.
* Order navigation and lists according to user importance.

## 10. End Flows Memorably: Peak-End Rule

Users judge an experience largely by its most intense moment and how it ends.

* Create a clear and satisfying completion state.
* Confirm what the user accomplished.
* Explain what happens next.
* Avoid ending flows on an empty or ambiguous screen.

## 11. Show Visible Progress: Zeigarnik Effect

Incomplete tasks remain mentally active and encourage users to return.

* Clearly show completed and unfinished steps.
* Save progress whenever possible.
* Make it easy to resume interrupted tasks.
* Use checklists or completion states for multi-step work.

## 12. Simplify Complex Interfaces: Law of Prägnanz

People interpret complex or ambiguous designs in the simplest form possible.

* Prefer simple structures and recognizable shapes.
* Remove unnecessary decoration and visual noise.
* Create an obvious visual hierarchy.
* Make the interface understandable at a glance.

## 13. Use Sensible Defaults: Hick's Law

Helpful defaults reduce the number of decisions users must make.

* Preselect the safest and most common option.
* Use existing context to reduce unnecessary input.
* Never use defaults that create unexpected commitments.
* Make every default easy to change.

## 14. Prevent Errors Proactively: Postel's Law

Interfaces should accept reasonable variations in user input while producing clear, predictable results.

* Accept common input formats and variations.
* Explain requirements before submission.
* Disable impossible or unavailable actions.
* Warn users before risky or destructive actions.

## 15. Make Errors Recoverable: Postel's Law

The interface should handle user mistakes gracefully without creating unnecessary failure.

* Preserve the user's work after an error.
* Explain what went wrong in plain language.
* Tell the user exactly how to fix it.
* Provide undo, retry, restore, or cancel options where appropriate.

## 16. Maintain Pattern Consistency: Law of Similarity

Elements that look similar are perceived as having related purposes.

* Give similar components the same appearance and behavior.
* Use consistent colors, labels, icons, spacing, and interaction states.
* Do not use the same visual treatment for different actions.
* Reuse established components before creating new ones.

## 17. Connect Related Elements Visually: Law of Uniform Connectedness

Visually connected elements are perceived as more closely related.

* Use containers, lines, backgrounds, or shared states to show relationships.
* Visually connect controls to the content they affect.
* Keep unrelated elements visually separate.
* Use connection deliberately, not decoratively.

## 18. Reduce Task Completion Time: Parkinson's Law

Tasks tend to expand to consume the time made available for them.

* Minimize the number of steps required.
* Remove unnecessary confirmations and screens.
* Prefill information the user has already provided.
* Offer shortcuts for frequent or repeat actions.

## 19. Reveal Complexity Gradually: Tesler's Law

Every system contains some complexity that cannot be removed, only managed or transferred.

* Show essential controls first.
* Reveal advanced options only when relevant.
* Let the system handle complexity whenever possible.
* Do not force users to understand internal technical details.

## 20. Make Completion Feel Closer: Goal-Gradient Effect

Motivation increases as users perceive themselves getting closer to a goal.

* Show progress throughout multi-step flows.
* Divide long tasks into visible milestones.
* Emphasize progress already made.
* Make the remaining work feel specific and achievable.

## Implementation Requirements

When creating or revising an interface:

1. Identify the user's primary goal.
2. Design the shortest clear path to that goal.
3. Make the next action visually obvious.
4. Remove anything that distracts from task completion.
5. Provide immediate feedback after every interaction.
6. Prevent errors before they occur.
7. Preserve user work when something goes wrong.
8. Confirm clearly when the goal has been completed.

When laws appear to conflict, prioritize clarity, accessibility, user control, and successful task completion. Do not apply these laws mechanically. Use them to make deliberate decisions based on the user's context and goal.
