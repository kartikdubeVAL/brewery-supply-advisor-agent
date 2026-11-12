# Product Requirements Document (PRD)

**Title:** Alpenquell Brauerei — Brewery Supply Planning Agent  
**Date:** 2026-11-14  
**Owner:** Supply Chain Planning  
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**  
Supply planners at Alpenquell Brauerei currently spend up to 2 hours manually cross-referencing tank inventory, QC lab status, regional brewery allocation rules, and packaging line capacity to answer a single demand-coverage question. This agent answers those questions in under 5 minutes via natural language — giving planners instant, rule-correct decisions when heat waves, events, or promotions create short-term demand uplifts.

**Business Need:**  
During summer peaks (calendar weeks CW25–CW31, 2027), the brewing network holds significant beer volume in fermentation and maturation tanks. Whether that volume can cover a specific demand uplift depends on four interrelated constraints: QC release status, regional brewery-to-region mapping, free (uncommitted) tank volume, and packaging line availability. Today planners resolve this manually, creating bottlenecks and decision delays. An agent that knows the business rules and has the data in context eliminates that bottleneck.

**Expected Value:**  
- Answer time per coverage question: 2 hours → 5 minutes
- Consistent, rule-correct assessments (no missed QC holds, no cross-regional assignments)
- Planners can focus on acting on the answer rather than finding it

**Product Objectives (Prioritized):**
1. Reduce demand coverage assessment time from 2 hours to 5 minutes for summer 2027 uplift events
2. Enforce all brewery business rules consistently (QC status, regional allocation, packaging capacity)
3. Provide transparent, data-grounded answers — only from the loaded Excel data, never invented

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to answer a demand coverage question | 2 hours | 5 minutes | Summer 2027 (CW25–CW31) | Short-term demand uplift assessment | user |

---

## User Profiles & Personas

### Primary Persona: Supply Planner

Lena, 34, Supply Planner at Alpenquell Brauerei. She manages short-term supply coverage for the South and West regions. Every summer she handles 5–10 demand uplift events triggered by weather forecasts, sponsored events, and trade promotions. Each event requires her to open multiple spreadsheets, check which tanks are QC-released, confirm they are in the right brewery region, calculate free volume, and verify there is packaging line capacity left — all while the commercial team is waiting for a go/no-go decision. She is comfortable with Excel, uses SAP for formal planning runs, but has no time for deep analysis. She needs a fast, trusted answer: "Yes, we can cover it with tanks X, Y, Z — here is the gap."

### Secondary Persona: Demand Planner

Marco, 41, Demand Planner. He runs the weekly S&OP review and needs to understand the cumulative upside and gap position across all regions and brands for the summer. He asks summary questions ("Which tanks should the lab release first to maximise coverage?") and uses the output to prioritise QC lab work and communicate risk to the commercial team.

---

## User Goals & Tasks

### For Lena (Supply Planner):

**Goals:**
- Get a coverage decision (Yes / No / Partially) with gap or surplus in hl within minutes
- Understand which tanks are secured and which are upside only
- Know why a tank is excluded and what to do about it

**Key Tasks:**
- Ask "Can we cover X hl of [brand] demand in [region] for CW[n]–CW[m]?"
- Ask "What is in tank [ID]?" to inspect a specific tank
- Ask "Why is tank [ID] not usable?" to understand a QC hold

### For Marco (Demand Planner):

**Goals:**
- Identify which Pending tanks should be prioritised for QC lab release
- Assess total coverage risk across all uplift events for the summer

**Key Tasks:**
- Ask "Which tanks should the lab release first?"
- Ask "What is the total coverage gap for the South in CW27–CW28?"

---

## Product Principles

1. **Data-grounded only**: The agent answers exclusively from the loaded Excel data. It never invents tanks, volumes, or breweries. When data is absent, it says so.
2. **Direct answer first**: Every response leads with Yes / No / Partially and the hl figure before any explanation — planners need the decision, not a narrative.
3. **Rules are non-negotiable**: QC status, regional allocation, and packaging line constraints are always applied. No answer bypasses a business rule.
4. **Transparency on exclusions**: Every excluded tank is named with its reason (QC note for Hold, region mismatch, insufficient free volume).
5. **Language follows the user**: Responses are always in the language the user writes in.

---

## Goals and Non-Goals

### Goals (In Scope)

- Parse and use the Excel workbook (Demand Uplift, Packaging Lines, Tank Inventory sheets) as the sole data source
- Answer natural language demand-coverage questions for summer 2027 uplift events (CW25–CW31)
- Apply all business rules: QC status (Released / Pending / Hold), regional brewery mapping, free volume only, packaging line capacity
- Return structured answers: coverage verdict + hl gap/surplus + secured tank list + upside tank list + Hold exclusions with QC note + one recommendation
- Respond in the user's language

### Non-Goals (Out of Scope)

- Integration with SAP S/4HANA, SAP IBP, or any ERP/planning system
- Writing back to the Excel file or creating production orders
- Updating demand forecasts or base plan allocations
- Handling planning periods outside CW25–CW31 summer 2027
- User authentication or multi-tenancy management

---

## Requirements

### Must-Have Requirements

**R01: Excel Data Loading**

- **Problem to Solve**: The agent has no data without the workbook; it cannot answer any question until the three sheets are parsed and in memory.
- **User Story**: As a supply planner, I need the agent to load the Excel workbook at startup so that all tank, demand, and packaging data is immediately available for querying.
- **Acceptance Criteria**:
  - Given the Excel file is present at the configured path, when the agent starts, then all three sheets (Demand Uplift, Packaging Lines, Tank Inventory) are parsed into structured in-memory data.
  - Given a sheet is missing or malformed, when the agent starts, then it reports the issue clearly and refuses to answer coverage questions.
- **Maps to Objective**: 1, 2
- **Priority Rank**: 1

**R02: QC Status Classification**

- **Problem to Solve**: Not all tanks are usable; planners need the agent to enforce QC rules automatically so they never accidentally rely on a Pending or Hold tank as secured supply.
- **User Story**: As a supply planner, I need the agent to classify each tank by its QC status so that only Released tanks count as secured supply.
- **Acceptance Criteria**:
  - Given a tank with QC status = Released, when it is evaluated for coverage, then it counts as secured supply (free volume only).
  - Given a tank with QC status = Pending, when it is evaluated, then it counts as upside only and is clearly labelled as such.
  - Given a tank with QC status = Hold, when it is evaluated, then it is excluded from coverage and the QC note is given as the reason.
- **Maps to Objective**: 2
- **Priority Rank**: 2

**R03: Regional Brewery Allocation**

- **Problem to Solve**: Beer can only be supplied from breweries in the same region; cross-regional assignments would violate logistics constraints.
- **User Story**: As a supply planner, I need the agent to enforce regional brewery mapping so that demand in a region is only matched to tanks from breweries in that region.
- **Acceptance Criteria**:
  - Given a demand uplift in the South region, when the agent searches for tanks, then it considers only tanks from Munich and Nuremberg breweries.
  - Given a demand uplift in the West region, then only Dortmund tanks are considered.
  - Given a demand uplift in the East region, then only Leipzig tanks are considered.
  - Tanks from non-matching breweries are excluded and, if asked, the agent states the region mismatch as the reason.
- **Maps to Objective**: 2
- **Priority Rank**: 3

**R04: Ready Week and Free Volume Check**

- **Problem to Solve**: A tank may be in the right region and QC-released but not yet ready, or its free volume may be zero (fully allocated to the base plan).
- **User Story**: As a supply planner, I need the agent to check that a tank's ready week is on or before the demand week and that its free volume is positive so that only actually available volume is counted.
- **Acceptance Criteria**:
  - Given a Released tank with ready week ≤ the demand week and free volume > 0, when evaluated, then its free volume is included in secured supply.
  - Given a Released tank with ready week > the demand week, when evaluated, then it is excluded for that week.
  - Given a tank with free volume = 0, when evaluated, then it contributes 0 hl to coverage.
- **Maps to Objective**: 2
- **Priority Rank**: 4

**R05: Packaging Line Capacity Check**

- **Problem to Solve**: Even if tank volume is available, coverage fails if there is insufficient packaging line capacity at the relevant breweries for the required weeks.
- **User Story**: As a supply planner, I need the agent to verify packaging line free capacity at the relevant breweries for the relevant weeks so that the coverage answer accounts for the full production path.
- **Acceptance Criteria**:
  - Given secured tank volume available, when the agent computes coverage, then it checks total free packaging line capacity at the matching breweries for each demand week.
  - Given packaging capacity is less than the secured tank volume, then the agent reports the lower figure as the effective coverage and flags the packaging constraint.
  - Given packaging capacity is sufficient, then no packaging warning is raised.
- **Maps to Objective**: 2
- **Priority Rank**: 5

**R06: Natural Language Coverage Q&A**

- **Problem to Solve**: Planners need to ask coverage questions in plain language without knowing query syntax or table structures.
- **User Story**: As a supply planner, I need to ask demand coverage questions in natural language and receive a structured, actionable answer so that I can make a go/no-go decision immediately.
- **Acceptance Criteria**:
  - Given a question such as "Can we cover the extra 2,400 hl Pils demand in the South for CW27–CW28?", when the agent responds, then the answer includes: coverage verdict (Yes / No / Partially), gap or surplus in hl, list of secured tank IDs and their contributed hl, list of upside (Pending) tank IDs, list of excluded Hold tanks with QC notes, packaging line status, and one recommendation.
  - Given a question about a single tank ("What is in tank MUC-T001?"), then the agent returns that tank's details from the inventory.
  - Given a question about a tank's exclusion reason ("Why is tank NUE-T006 not usable?"), then the agent returns the specific reason (QC status + note, region mismatch, or not yet ready).
  - Given a prioritisation question ("Which tanks should the lab release first?"), then the agent ranks Pending tanks by their potential coverage contribution.
- **Maps to Objective**: 1, 3
- **Priority Rank**: 6

**R07: Data-Grounding Guardrail**

- **Problem to Solve**: Planners must trust that every figure the agent cites is from the actual data, not hallucinated.
- **User Story**: As a supply planner, I need the agent to answer only from the loaded data so that I can trust every hl figure and tank ID it gives me.
- **Acceptance Criteria**:
  - Given a question about a tank or volume not present in the data, when the agent responds, then it states that the information is not in the data — it does not invent an answer.
  - Given any coverage answer, then every tank ID, volume figure, and brewery name cited can be traced to a row in the loaded Excel data.
- **Maps to Objective**: 3
- **Priority Rank**: 7

**R08: Multilingual Responses**

- **Problem to Solve**: Planners across regions may write in German or English; the agent must respond in kind.
- **User Story**: As a supply planner, I need the agent to reply in my language so that I can read answers without translation effort.
- **Acceptance Criteria**:
  - Given a question written in German, when the agent responds, then the answer is in German.
  - Given a question written in English, then the answer is in English.
- **Maps to Objective**: 1
- **Priority Rank**: 8

---

## Solution Architecture

**Architecture Overview:**  
A single Python AI agent (A2A protocol) deployed on SAP AI Core via Joule Studio. The Excel workbook is loaded at agent startup into structured in-memory data. The agent exposes a set of tools that query this in-memory dataset and apply the business rules. No external API integrations are required; all data originates from the Excel file.

**Key Components:**

- **Agent runtime**: Python A2A agent on SAP AI Core / Joule Studio
- **Data loader**: Startup module that reads the Excel workbook and parses all three sheets into typed in-memory structures
- **Business rule engine**: Rule functions implementing QC classification, regional brewery mapping, ready-week/free-volume check, and packaging line capacity check
- **Tool set**: Agent-callable tools (query demand uplift, inspect tank, check coverage, list pending tanks, check packaging capacity)
- **Response composer**: Formats structured coverage answers (verdict, hl gap/surplus, tank IDs, upside list, Hold exclusions, recommendation)

**Integration Points:**

- Excel workbook (read-only at startup): the sole external data source; no live API connections

**Deployment Environments:**

- Development: local execution with test Excel fixture
- Production: SAP AI Core via Joule Studio; Excel file provisioned as a static asset

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The data loader is designed to accept additional sheets or columns without agent core changes, enabling future inclusion of batch records, logistics data, or additional QC fields.
- Business rules are implemented as isolated, testable functions — new rules (e.g., minimum shelf life, additional regions) can be added without modifying the Q&A layer.
- The tool set is additive: new tools (e.g., "check transport availability") can be registered without changing existing tools.
- Future integration with SAP S/4HANA or SAP IBP APIs can replace the Excel data loader without changing the business rule or agent conversation layer.

**Business Step Instrumentation:**
All five key business milestones must be instrumented with structured log statements for observability (OpenTelemetry spans in production). See the Milestones section for the full log specification.

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent — the agent reasons over data and applies rules without human intervention; it proposes a recommendation but does not execute any action (read-only).

**Actions the system performs without human approval:**
- Parsing and loading the Excel workbook at startup
- Classifying tanks by QC status, region, ready week, and free volume
- Computing coverage totals and packaging capacity checks
- Composing and returning a structured coverage answer

**Actions that require human review or approval:**
- All supply decisions (the agent gives the recommendation; the planner acts on it)
- Updating the Excel file or any upstream system

**Model or engine used:** Large language model via SAP Generative AI Hub (model selection per Joule Studio deployment configuration)

**Knowledge & data sources accessed:**
- Excel workbook (Demand Uplift sheet): region, brand, week range, extra demand in hl
- Excel workbook (Packaging Lines sheet): line ID, brewery, format, free capacity in hl per week
- Excel workbook (Tank Inventory sheet): tank ID, brewery, region, brand, ready week, total volume, allocated volume, free volume, QC status, QC note

**Tools or connectors invoked:**
- `load_workbook`: reads and parses the Excel file at startup — read-only, no side effects
- `query_demand_uplift`: retrieves demand uplift entries matching region, brand, and week range — read-only
- `inspect_tank`: returns all fields for a specific tank ID — read-only
- `check_coverage`: applies QC, regional, ready-week, free-volume, and packaging-line rules to compute coverage for a given uplift event — read-only, core reasoning tool
- `list_pending_tanks`: returns Pending tanks ranked by coverage potential for QC prioritisation — read-only

**Guardrails & fail-safes:**
- The agent never invents data: all tank IDs, volumes, and brewery names in responses must be traceable to a loaded Excel row
- If the Excel file is missing or unparseable at startup, the agent refuses coverage queries and reports the data issue
- Hold tanks are never included in secured or upside coverage under any circumstances; their QC note is always surfaced
- The agent takes no write actions — it cannot modify the Excel file, create orders, or update any system
- When a question falls outside the data (unknown tank ID, brand not in the file), the agent explicitly states the data is not available

---

## Milestones

### M1: Data Loaded

- **Description**: The Excel workbook has been parsed and all three sheets are available as structured in-memory data.
- **Achieved when**: All three sheets (Demand Uplift, Packaging Lines, Tank Inventory) are successfully parsed with at least one row each.
- **Log on achievement**: `M1.achieved: Excel workbook loaded — {demand_rows} demand uplift rows, {tank_rows} tanks, {line_rows} packaging lines`
- **Log on miss**: `M1.missed: Excel workbook could not be loaded — {error_detail}`

### M2: QC Rules Applied

- **Description**: Each tank in the inventory has been classified as Released (secured supply), Pending (upside), or Hold (excluded) per the business rules.
- **Achieved when**: All tanks have a QC classification label applied and Hold tanks have their QC note extracted.
- **Log on achievement**: `M2.achieved: QC classification complete — {released_count} Released, {pending_count} Pending, {hold_count} Hold`
- **Log on miss**: `M2.missed: QC classification failed — {error_detail}`

### M3: Regional Allocation Validated

- **Description**: The brewery-to-region mapping has been applied to filter tanks to those eligible for the target region.
- **Achieved when**: The candidate tank list contains only tanks whose brewery is in the correct region for the demand uplift being assessed.
- **Log on achievement**: `M3.achieved: Regional filter applied for {region} — {eligible_tank_count} eligible tanks from {brewery_list}`
- **Log on miss**: `M3.missed: Regional allocation check failed — {error_detail}`

### M4: Packaging Line Capacity Checked

- **Description**: Free packaging line capacity at the relevant breweries has been retrieved and compared against the secured tank volume.
- **Achieved when**: A packaging capacity figure (in hl) is available for each relevant brewery and week combination.
- **Log on achievement**: `M4.achieved: Packaging capacity checked — effective capacity {capacity_hl} hl for {brewery_list} in {week_range}`
- **Log on miss**: `M4.missed: Packaging capacity check failed — {error_detail}`

### M5: Coverage Answer Delivered

- **Description**: The agent has composed and returned a structured coverage response to the planner.
- **Achieved when**: The response includes a verdict (Yes / No / Partially), hl gap or surplus, secured tank IDs, upside tank list, Hold exclusions with QC notes, and one recommendation.
- **Log on achievement**: `M5.achieved: Coverage answer delivered — {verdict}, secured {secured_hl} hl, gap/surplus {delta_hl} hl, {tank_count} tanks cited`
- **Log on miss**: `M5.missed: Coverage answer could not be composed — {error_detail}`

---

## Non-Functional Requirements

### Performance

- **Latency**: Coverage answers returned within 30 seconds (target 5 minutes for the full planning task, with most time being human reading/decision time)
- **Throughput**: Designed for individual interactive use; no batch-query requirements

### Reliability

- **Availability**: Follows SAP AI Core / Joule Studio SLA
- **Fallback**: If the data file is unavailable at startup, the agent reports the failure clearly and declines coverage queries rather than returning incorrect results

### Explainability

- **Traceability**: Every hl figure and tank ID in a response is traceable to a specific Excel row
- **Decision Logging**: All five milestones emit structured log entries for observability
- **Uncertainty Communication**: When data is absent or ambiguous, the agent explicitly states that the information is not available in the loaded data

---

## Risks, Assumptions, and Dependencies

### Risks

- **Data quality**: If the Excel file contains errors (wrong QC status, missing ready week), the agent will propagate those errors into its answers. Mitigation: document data ownership and validation responsibility with the supply planning team.
- **Scope creep**: Planners may request live ERP data or write-back capability once the agent is in use. Mitigation: Out-of-scope items are explicitly listed; extensions require a new project phase.

### Assumptions

- The Excel workbook is the single authoritative source for tank inventory, demand uplifts, and packaging line capacity for summer 2027.
- The brewery-to-region mapping (South = Munich + Nuremberg, West = Dortmund, East = Leipzig) is fixed for the summer 2027 planning horizon.
- The agent is accessed interactively by individual supply planners; no concurrent high-volume query load is expected.

### Dependencies

- Excel workbook provisioned and available at the agent's configured file path before deployment
- SAP AI Core / Joule Studio environment available for agent deployment

---

## Appendix

### Glossary

| Term | Definition |
|------|-----------|
| hl | Hectolitre — the unit of volume used throughout (1 hl = 100 litres) |
| Free volume | Tank total volume minus allocated volume; the uncommitted portion available for demand uplift coverage |
| Allocated volume | Volume already committed to the base demand plan; not available for uplifts |
| Ready week | The calendar week in which the tank's beer is ready for packaging |
| QC status | Quality control release status: Released (usable), Pending (lab result awaited), Hold (blocked, reason in QC note) |
| Secured supply | Volume confirmed available for an uplift: Released tanks only, free volume only, ready week ≤ demand week, packaging capacity sufficient |
| Upside | Additional volume that could become secured supply if Pending tanks are released by the lab in time |
| CW | Calendar week (ISO 8601), e.g. CW27 = the 27th week of the year |
| Demand uplift | Extra demand in hl on top of the base plan, triggered by heat waves, events, or promotions |
