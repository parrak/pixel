# Citron Health Phase 4: HoldCo Command Center

## Reframe

Phase 3 answered how an acquired specialty RCM operator works inside Citron.

Phase 4 answers why owning Citron increases the value of a specialty RCM platform.

The product center of gravity moves from operator enablement alone to the full value-creation loop:

- acquisition
- standardization
- operational improvement
- knowledge compounding
- EBITDA expansion
- enterprise value creation

## Objective

Make the rollup thesis visible to:

- private equity partners
- operating partners
- acquisition targets
- future executives
- board members

The software should show how acquired operators become standardized, how operational improvements
become EBITDA, and how those learnings compound across the portfolio.

## Architecture Additions

### HoldCo Layer

- Introduce a HoldCo concept above organizations
- Roll synthetic organizations into one portfolio dashboard
- Surface portfolio revenue, EBITDA, operational risks, bottlenecks, and value creation progress

### Value Creation System

- Add first-class value-creation initiatives
- Tie operating changes to expected and realized EBITDA impact
- Keep ownership, target state, current state, timeline, and workflow links visible

### Benchmarking

- Compare organizations against portfolio average, top quartile, and best-in-class
- Focus on collection rate, denial rate, AR aging, coder productivity, authorization cycle time,
  revenue per employee, margin, and recovery rate

### Playbooks

- Add reusable operating playbooks that can be applied across acquisitions
- Capture tasks, owners, dependencies, expected outcomes, financial impact, and historical results

### Decision Intelligence

- Expand recommendation -> decision -> outcome into a portfolio learning layer
- Roll up which decisions work, which fail, and which patterns create value

### Acquisition Integration

- Turn the simulator into a post-acquisition integration center
- Generate current-state assessment, workflow gaps, technology gaps, operating risks, 90-day roadmap,
  and value-creation opportunities

### Executive Review

- Create a board-style operating review from the same synthetic portfolio payload
- Include executive summary, financial performance, operational performance, wins, risks, and required decisions

## Product Surface Changes

### Streamlit

- Add HoldCo Command Center
- Add Value Creation, Benchmarks, Playbooks, and Executive Review surfaces
- Preserve role queues, workflow engine, acquisition simulator, and legacy Phase 3 modules

### Public Site and Demo

- Shift messaging from operator operating system to HoldCo command center
- Show how Citron compounds value across acquisitions
- Keep the existing Citron visual system and branding intact

### Fallback Vercel Experience

- Expose the same HoldCo thesis and payload through the fallback pages and JSON endpoints
- Keep synthetic-only guardrails in place

## Acceptance Criteria

- A first-time PE or operating partner user understands what leadership should focus on today
- Citron visibly links workflow changes to EBITDA impact
- Operational variance is obvious across organizations
- Playbooks and benchmarks read as reusable portfolio infrastructure rather than one-off demos
- The platform feels like a specialty RCM HoldCo operating system, not a point workflow copilot
