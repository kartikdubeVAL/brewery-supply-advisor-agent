# Alpenquell Brauerei Brewery Supply Planning Agent

Alpenquell Brauerei (fictional demo company) — AI agent for short-term demand uplift coverage assessment in summer 2027.

## Business challenge

Supply planners at Alpenquell Brauerei need to quickly determine whether beer already in fermentation and maturation tanks can cover short-term demand uplifts caused by heat waves, events, and promotions in summer 2027 (calendar weeks CW25–CW31). The assessment requires applying QC status rules (Released / Pending / Hold), regional brewery allocation constraints (South = Munich + Nuremberg, West = Dortmund, East = Leipzig), and packaging line capacity checks — all of which currently take planners up to 2 hours per question.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to answer a demand coverage question | 2 hours | 5 minutes | Summer 2027 (CW25–CW31) | Short-term demand uplift assessment | user |

## Key Milestones

1. **Data loaded** — Excel file parsed: Demand Uplift, Packaging Lines, and Tank Inventory sheets available to the agent.
2. **QC rules applied** — Agent correctly classifies tanks as secured supply (Released), upside (Pending), or excluded (Hold) per business rules.
3. **Regional allocation validated** — Agent enforces brewery-to-region mapping (South / West / East) when matching tanks to demand.
4. **Packaging line capacity checked** — Agent verifies free line capacity at the relevant breweries for the relevant weeks.
5. **Coverage answer delivered** — Agent responds with Yes / No / Partially, the gap or surplus in hl, tank IDs used, upside tanks, Hold exclusions with QC note, and one clear recommendation.

## Business Architecture (RBA)

### End-to-End Process

Plan to Fulfill (generic)

### Process Hierarchy

```
Plan to Fulfill (E2E)
└── Plan to Optimize Fulfillment
    └── Align demand, supply and financial plans (BPS-327)
        └── Perform sales and operations planning
    └── Plan demand (BPS-338)
        └── Generate collaborative demand plan
└── Make to Inspect
    └── Operate manufacturing (BPS-347)
        └── Confirm production
        └── Perform quality inspection
        └── Start production
└── Deliver Product to Fulfill
    └── Manage warehouse and inventory (BPS-348)
        └── Perform quality inspection
    └── Perform order promising (BPS-353)
        └── Manage product availability
```

### Summary

The brewery demand uplift coverage challenge maps to the Plan to Fulfill E2E: planners align demand and supply (BPS-327, BPS-338), check QC status and tank readiness (BPS-347, BPS-348), and apply regional allocation and capacity constraints (BPS-353) — best matched by the generic Plan to Fulfill E2E with process-industry Make-to-Stock variants.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ------------------ | ------------------- | ---- | ------------------- |
| Align demand and supply plans | SAP Integrated Business Planning (S&OP) | — | — | — | — | — | Yes | IBP covers formal S&OP; does not handle ad-hoc natural language queries over Excel tank data |
| QC status–based tank eligibility | SAP S/4HANA Cloud (Quality Inspection) | — | — | — | — | — | Yes | S/4HANA manages QC in ERP; brewery uses Excel-based inventory; custom rule logic required |
| Regional brewery allocation rules | SAP Order Management (Order Promising) | — | — | — | — | — | Yes | No standard product encodes the South/West/East brewery mapping; must be implemented in agent |
| Packaging line capacity check | SAP Digital Manufacturing / S/4HANA | — | — | — | — | — | Yes | Standard products cover production execution; agent must read free capacity from Excel |
| Natural language coverage Q&A | — | — | — | — | — | — | Yes | No standard SAP product provides conversational uplift coverage assessment; custom AI agent required |

### Key findings

- Standard SAP products (SAP IBP, S/4HANA, SAP Digital Manufacturing) cover the formal supply planning and manufacturing execution processes but do not address the conversational, rule-based, Excel-driven use case.
- No MCP server or OData API was identified that directly exposes tank inventory, QC status, or packaging line data in the Alpenquell landscape; all data resides in an Excel file.
- The entire solution is a custom development gap: a Python AI agent that reads the Excel file at startup and reasons over it using brewery-specific business rules.
- API discovery timed out (504); no pre-built integrations were found that could substitute for the Excel-based data model.
- The agent must strictly enforce the data-grounding rule: answer only from the Excel data, never invent tanks, volumes, or breweries.

## Recommendations

### Python AI Agent for Brewery Supply Coverage Assessment

#### Executive Summary

Custom Python AI agent that reads Excel tank data and answers natural language coverage questions.

#### Recommended Solution

Build a Python AI agent (A2A protocol) that loads the Excel workbook (three sheets: Demand Uplift, Packaging Lines, Tank Inventory) at startup and exposes tools for supply planners to query demand coverage. The agent applies the brewery-specific business rules (QC status, regional allocation, packaging line capacity) and returns structured, direct answers with tank IDs, volumes, and one recommendation. Deployed on SAP AI Core via Joule Studio.

#### Recommended solution category

AI Agent

#### Intent fit

95%
