---
name: brewery-coverage-rules
description: Business rules for Alpenquell Brauerei demand coverage assessment — QC classification, regional brewery allocation, packaging line checks, and structured answer format
---

# Brewery Coverage Rules

## When to Use This Skill

Load this skill whenever you are:
- Answering a demand coverage question (Can we cover X hl of [brand] in [region] for CW[n]?)
- Asked to explain why a tank is not usable
- Asked to prioritise tanks for lab release
- Assessing whether packaging capacity is sufficient

## QC Status Rules

| QC Status | How to Count | Notes |
|-----------|-------------|-------|
| Released  | Secured supply — use free volume only | Allocated volume is already committed to the base plan; never count it |
| Pending   | Upside only — label clearly as "possible if lab releases in time" | Never count as secured supply |
| Hold      | Excluded — always state the QC note as the reason | Never count, not even as upside |

**Rule**: A tank counts as secured supply for a week only if ALL of the following are true:
1. QC status = Released
2. ready_week ≤ demand_week
3. free_volume_hl > 0

## Regional Brewery Allocation

Beer can ONLY be supplied from breweries in the same region as the demand. Cross-regional assignments are never allowed.

| Region | Allowed Breweries | Brewery Code Prefixes |
|--------|------------------|-----------------------|
| South  | Munich, Nuremberg | MUC, NUE |
| West   | Dortmund | DOR |
| East   | Leipzig | LEI |

If a tank's brewery does not match the demand region, exclude it and state "region mismatch" as the reason.

## Tank Eligibility Check (Step by Step)

For each tank in the inventory when evaluating a demand uplift:

1. Check region match: Does the tank's brewery belong to the demand region? If not → exclude (region mismatch)
2. Check brand match: Does the tank's brand match the demand brand? If not → skip
3. Check QC status:
   - Hold → exclude, record QC note
   - Pending → mark as upside, continue
   - Released → continue to step 4
4. Check ready week: Is ready_week ≤ demand_week? If not → exclude for that week
5. Check free volume: Is free_volume_hl > 0? If not → contributes 0 hl
6. Count free_volume_hl toward secured supply

## Coverage Calculation

Follow this order exactly:

1. Filter tanks: keep only those matching region AND brand
2. Apply QC rules: classify each as secured / upside / excluded
3. Apply ready-week and free-volume check on secured tanks
4. Sum free_volume_hl of all eligible secured (Released) tanks → secured_hl
5. Check packaging line free capacity at the matching breweries for the demand week(s):
   - effective_coverage_hl = min(secured_hl, total_packaging_free_capacity_hl)
   - If packaging_capacity < secured_hl → flag packaging constraint, effective coverage is lower
6. Compare effective_coverage_hl to demand uplift hl:
   - effective_coverage_hl ≥ demand_hl → Yes (surplus = effective_coverage_hl - demand_hl)
   - effective_coverage_hl = 0 → No (gap = demand_hl)
   - 0 < effective_coverage_hl < demand_hl → Partially (gap = demand_hl - effective_coverage_hl)

## Answer Format

Every coverage answer MUST follow this structure. Be concise. Answer in the user's language.

```
[VERDICT]: [gap or surplus in hl]

Secured supply ([secured_hl] hl):
- [tank_id] ([brewery]): [free_volume_hl] hl  ← repeat per tank

Upside (Pending — usable if lab releases in time):
- [tank_id] ([brewery]): [free_volume_hl] hl  ← repeat, or "None"

Excluded (Hold):
- [tank_id]: [qc_note]  ← repeat, or "None"

Packaging lines ([brewery_list], CW[n]–CW[m]):
- Free capacity: [packaging_capacity_hl] hl  ← state if this limits effective coverage

Recommendation: [one clear sentence]
```

**Verdict examples:**
- "Yes — surplus of 800 hl"
- "No — gap of 2,400 hl (no Released tanks available in region)"
- "Partially — gap of 600 hl (secured 1,800 hl of 2,400 hl needed)"

## Data-Grounding Rule

Every tank ID, volume figure, brewery name, and QC note in your answer MUST come from the loaded Excel data.
If a tank, brand, or region is not in the data, say: "This information is not available in the loaded inventory data."
Never invent, estimate, or extrapolate data.
