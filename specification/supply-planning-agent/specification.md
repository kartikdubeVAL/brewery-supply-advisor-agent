# Specification: supply-planning-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` to understand the full business context before writing any code
- [x] Bootstrap agent code in `assets/supply-planning-agent/` using the `sap-agent-bootstrap` section instructions (invoke from inside `assets/supply-planning-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies; validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

This agent has complex domain-specific business rules (QC classification, regional allocation, coverage calculation) and a structured multi-step answer format. Create the following runtime skill:

- [x] Create `assets/supply-planning-agent/app/skills/brewery-coverage-rules/SKILL.md` with:
  - YAML frontmatter: `name: brewery-coverage-rules`, `description: Business rules for Alpenquell Brauerei demand coverage assessment — QC classification, regional brewery allocation, packaging line checks, and structured answer format`
  - **QC Status Rules section**: Released = secured supply (free volume only); Pending = upside only (never secured); Hold = excluded, always surface the QC note as the reason
  - **Regional Brewery Allocation section**: South → Munich (MUC) and Nuremberg (NUE) only; West → Dortmund (DOR) only; East → Leipzig (LEI) only; cross-regional assignments are never allowed
  - **Tank Eligibility section**: A tank counts toward secured supply only if QC = Released AND ready week ≤ demand week AND free volume > 0. Allocated volume is already committed to the base plan — never count it.
  - **Coverage Calculation section**: step-by-step instructions: (1) filter tanks by region and brand, (2) apply QC rules, (3) apply ready-week and free-volume check, (4) sum free volumes of Released tanks, (5) compare to packaging line free capacity (take the minimum of tank volume and packaging capacity as effective coverage), (6) compare effective coverage to demand uplift hl
  - **Answer Format section**: every coverage answer must follow this structure: verdict (Yes / No / Partially) + gap or surplus in hl, secured tank list with tank IDs and hl contributed, upside tank list (Pending), excluded Hold tanks with QC notes, packaging line status, one clear recommendation. Short answers, in the user's language.
  - **Data-Grounding Rule section**: every tank ID, volume figure, and brewery name cited must come from the loaded Excel data. If information is not in the data, say so — never invent.

- [x] Create companion reference file `assets/supply-planning-agent/app/skills/brewery-coverage-rules/references/region-brewery-map.md` with a markdown table mapping each region to its breweries and brewery code prefixes (South: Munich MUC, Nuremberg NUE; West: Dortmund DOR; East: Leipzig LEI)

---

## Project-Specific Tasks

### Excel Data Loading

- [x] Add `openpyxl` to `requirements.txt` for Excel file parsing
- [x] Create `assets/supply-planning-agent/app/workbook_loader.py` that:
  - Reads the Excel workbook from a configurable path (environment variable `BREWERY_EXCEL_PATH`, default `data/brewery_supply_data.xlsx`)
  - Parses the **Demand Uplift** sheet into a list of typed dicts with fields: `region`, `brand`, `week_start`, `week_end`, `extra_demand_hl`
  - Parses the **Packaging Lines** sheet into a list of typed dicts with fields: `line_id`, `brewery`, `format`, `free_capacity_hl_per_week`
  - Parses the **Tank Inventory** sheet into a list of typed dicts with fields: `tank_id`, `brewery`, `region`, `brand`, `ready_week`, `total_volume_hl`, `allocated_volume_hl`, `free_volume_hl`, `qc_status`, `qc_note`
  - Validates that all three sheets are present; raises a clear `ValueError` if any sheet is missing
  - Returns a `BreweryData` dataclass (or named tuple) holding all three lists
  - Is called once at agent startup and stored as module-level state — not re-read on every query
- [x] Create `assets/supply-planning-agent/app/data/brewery_supply_data.xlsx` — a minimal demo Excel workbook with:
  - **Demand Uplift** sheet: at least 3 rows covering regions South, West, East with brands Pils and Weizen across CW25–CW31
  - **Packaging Lines** sheet: at least 4 rows covering Munich, Nuremberg, Dortmund, Leipzig breweries
  - **Tank Inventory** sheet: at least 8 rows covering all breweries, a mix of QC statuses (Released, Pending, Hold), various ready weeks within CW25–CW31, and varying free/allocated volumes

### Business Rule Engine

- [x] Create `assets/supply-planning-agent/app/business_rules.py` that implements:
  - `classify_tank_qc(tank: dict) -> str` — returns `"secured"`, `"upside"`, or `"excluded"` based on QC status
  - `get_eligible_breweries(region: str) -> list[str]` — returns brewery list for the region (South: Munich + Nuremberg; West: Dortmund; East: Leipzig); raises `ValueError` for unknown regions
  - `is_tank_ready(tank: dict, demand_week: int) -> bool` — returns True if `ready_week <= demand_week` and `free_volume_hl > 0`
  - `compute_coverage(demand_hl: float, tanks: list[dict], packaging_lines: list[dict], region: str, brand: str, week_start: int, week_end: int) -> dict` — applies all rules and returns a coverage result dict with keys: `verdict` (Yes/No/Partially), `secured_hl`, `gap_hl` (positive = shortfall, negative = surplus), `secured_tanks` (list of dicts with tank_id and contributed_hl), `upside_tanks` (list of tank_ids), `excluded_hold_tanks` (list of dicts with tank_id and qc_note), `packaging_capacity_hl`, `packaging_limited` (bool), `recommendation` (string)

### Agent Tools

- [x] Create `assets/supply-planning-agent/app/tools/` directory with one file per tool:

- [x] `assets/supply-planning-agent/app/tools/query_demand_uplift.py` — tool `query_demand_uplift(region: str, brand: str, week_start: int, week_end: int) -> str`:
  - Searches the in-memory Demand Uplift data for rows matching region, brand, and overlapping week range
  - Returns a formatted string listing matching demand uplift entries (region, brand, weeks, extra_demand_hl) or "No demand uplift found for the given parameters"

- [x] `assets/supply-planning-agent/app/tools/inspect_tank.py` — tool `inspect_tank(tank_id: str) -> str`:
  - Looks up the tank by tank_id in the in-memory Tank Inventory (case-insensitive)
  - Returns all tank fields as a formatted summary, or "Tank [ID] not found in inventory"
  - If QC status is Hold, always includes the QC note

- [x] `assets/supply-planning-agent/app/tools/check_coverage.py` — tool `check_coverage(region: str, brand: str, demand_hl: float, week_start: int, week_end: int) -> str`:
  - Calls `compute_coverage` from `business_rules.py` with the loaded data
  - Returns a fully structured coverage answer in the format defined in the brewery-coverage-rules skill: verdict, gap/surplus in hl, secured tank list with IDs and hl, upside tanks, Hold exclusions with QC notes, packaging line status, and one recommendation
  - Loads the brewery-coverage-rules SKILL.md for answer formatting guidance

- [x] `assets/supply-planning-agent/app/tools/list_pending_tanks.py` — tool `list_pending_tanks(region: str, brand: str) -> str`:
  - Filters the Tank Inventory for QC = Pending tanks in the given region and brand
  - Ranks them by free_volume_hl descending (highest coverage potential first)
  - Returns a ranked list with tank_id, brewery, free_volume_hl, ready_week, and the potential contribution to coverage if released

- [x] `assets/supply-planning-agent/app/tools/list_demand_uplifts.py` — tool `list_demand_uplifts() -> str`:
  - Returns all demand uplift entries for the planning horizon (CW25–CW31)
  - Formatted as a summary table: region, brand, weeks, extra_demand_hl

### Agent System Prompt

- [x] Update the system prompt in `assets/supply-planning-agent/app/agent.py` to include:
  - Role: "You are the Alpenquell Brauerei supply planning assistant. You help supply planners determine whether beer in fermentation and maturation tanks can cover short-term demand uplifts in summer 2027 (CW25–CW31)."
  - Data-grounding rule: "IMPORTANT: Answer ONLY from the data loaded from the Excel workbook. Never invent tank IDs, volumes, breweries, or demand figures. If information is not in the data, say so explicitly."
  - Tool instruction: "Use the available tools to answer every question. Load the `brewery-coverage-rules` skill whenever you assess demand coverage or are asked about tank eligibility rules."
  - Answer format: "Lead every coverage answer with the verdict (Yes / No / Partially) and the gap or surplus in hl before any explanation. Answer in the language the user writes in."
  - Error relay: "If a tool returns an error, report the error message exactly as received."

### Data Wiring at Startup

- [x] In `assets/supply-planning-agent/app/agent.py` (or `main.py` if more appropriate), call `workbook_loader.load_workbook()` at agent startup and make the resulting `BreweryData` object available as module-level state accessible by all tools
- [x] Ensure all tool functions import the module-level `BreweryData` state rather than re-reading the file on each call
- [x] If the workbook cannot be loaded at startup, log the error clearly and raise so the agent fails fast rather than returning silent wrong answers

---

## Business Instrumentation

- [x] Implement the five PRD milestones as structured log statements and OpenTelemetry spans in the agent's business logic (extract into a plain async helper `_run_coverage_check()` — do NOT put spans inside async generators):

  - **M1 — Data Loaded**: emit on successful workbook parse
    - achieved: `M1.achieved: Excel workbook loaded — {demand_rows} demand uplift rows, {tank_rows} tanks, {line_rows} packaging lines`
    - missed: `M1.missed: Excel workbook could not be loaded — {error_detail}`

  - **M2 — QC Rules Applied**: emit when tank QC classification completes for a coverage query
    - achieved: `M2.achieved: QC classification complete — {released_count} Released, {pending_count} Pending, {hold_count} Hold`
    - missed: `M2.missed: QC classification failed — {error_detail}`

  - **M3 — Regional Allocation Validated**: emit after regional brewery filter is applied
    - achieved: `M3.achieved: Regional filter applied for {region} — {eligible_tank_count} eligible tanks from {brewery_list}`
    - missed: `M3.missed: Regional allocation check failed — {error_detail}`

  - **M4 — Packaging Line Capacity Checked**: emit after packaging capacity lookup
    - achieved: `M4.achieved: Packaging capacity checked — effective capacity {capacity_hl} hl for {brewery_list} in {week_range}`
    - missed: `M4.missed: Packaging capacity check failed — {error_detail}`

  - **M5 — Coverage Answer Delivered**: emit when structured response is returned
    - achieved: `M5.achieved: Coverage answer delivered — {verdict}, secured {secured_hl} hl, gap/surplus {delta_hl} hl, {tank_count} tanks cited`
    - missed: `M5.missed: Coverage answer could not be composed — {error_detail}`

- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

No SAP API integrations are required. All data is loaded from the Excel workbook at startup. There are no MCP servers to wire, no `api-specs/`, and no `mcp-specs/`. Skip all MCP server setup, `mcp-translation-file`, and `mcp-mock-config` tasks — they do not apply to this asset.

- [x] Confirm `asset.yaml` has no `requires` entries for MCP servers (the agent has no external API dependencies)

---

## Testing

- [x] Install test dependencies: `pip install -r requirements-test.txt` from `assets/supply-planning-agent/`
- [x] Create `assets/supply-planning-agent/tests/test_workbook_loader.py`:
  - Test: successful parse of a valid 3-sheet workbook returns correct row counts and field types
  - Test: missing sheet raises `ValueError` with a descriptive message
- [x] Create `assets/supply-planning-agent/tests/test_business_rules.py`:
  - Test: `classify_tank_qc` returns `"secured"` for Released, `"upside"` for Pending, `"excluded"` for Hold
  - Test: `get_eligible_breweries("South")` returns Munich and Nuremberg; `"West"` returns Dortmund; `"East"` returns Leipzig; unknown region raises `ValueError`
  - Test: `is_tank_ready` returns True when ready_week ≤ demand_week and free_volume > 0; False otherwise
  - Test: `compute_coverage` returns `verdict="Yes"` when Released tank volume ≥ demand_hl and packaging capacity ≥ demand_hl
  - Test: `compute_coverage` returns `verdict="No"` when no Released tanks are available
  - Test: `compute_coverage` returns `verdict="Partially"` when Released tank volume covers some but not all demand_hl
  - Test: Hold tanks appear in `excluded_hold_tanks` with their QC note; Pending tanks appear in `upside_tanks`
  - Test: packaging line constraint caps effective coverage when packaging capacity < tank volume
- [x] Create `assets/supply-planning-agent/tests/test_tool_query_demand_uplift.py` — unit test for `query_demand_uplift`
- [x] Create `assets/supply-planning-agent/tests/test_tool_inspect_tank.py` — unit test for `inspect_tank`
- [x] Create `assets/supply-planning-agent/tests/test_tool_check_coverage.py` — unit test for `check_coverage`
- [x] Create `assets/supply-planning-agent/tests/test_tool_list_pending_tanks.py` — unit test for `list_pending_tanks`
- [x] Create `assets/supply-planning-agent/tests/test_tool_list_demand_uplifts.py` — unit test for `list_demand_uplifts`
- [x] Create `assets/supply-planning-agent/tests/test_integration.py` — one end-to-end integration test:
  - Mocks the LLM (patch `ChatLiteLLM`) to return a canned coverage answer
  - Calls the agent's `invoke` function with a natural language coverage question (e.g. "Can we cover 2,400 hl Pils in the South for CW27?")
  - Asserts the agent calls `check_coverage` with the correct parameters
  - Asserts the response contains a verdict string
  - All external calls (AI Core, MCP) are mocked — test must run fully offline
- [x] Run `pytest` from `assets/supply-planning-agent/` (no args) — fix any failures before proceeding
- [x] If coverage < 70%, add targeted tests until threshold is met
- [x] Run `pytest` again from `assets/supply-planning-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/supply-planning-agent/`
