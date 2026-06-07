from __future__ import annotations

import json
from functools import lru_cache
from html import escape
from typing import Iterable
from urllib.parse import parse_qs

from asc_rcm_lite.copilot.ar_copilot import ARCopilot
from asc_rcm_lite.copilot.denial_copilot import DenialCopilot
from asc_rcm_lite.copilot.payer_intelligence_copilot import PayerIntelligenceCopilot
from asc_rcm_lite.copilot.workflow_assistant import WorkflowAssistant
from asc_rcm_lite.pipeline import DEFAULT_AS_OF_DATE, PipelineResult, run_pipeline


@lru_cache(maxsize=1)
def _load_result() -> PipelineResult:
    return run_pipeline(as_of_date=DEFAULT_AS_OF_DATE)


def _selected_case(case_id: str | None):
    result = _load_result()
    if case_id:
        for case in result.cases:
            if case.case_id == case_id:
                return case
    return result.cases[0]


def _json_response(start_response, payload: object, status: str = "200 OK"):
    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "public, max-age=60"),
        ],
    )
    return [body]


def _html_response(start_response, body: str, status: str = "200 OK"):
    raw = body.encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(raw))),
            ("Cache-Control", "public, max-age=60"),
        ],
    )
    return [raw]


def _serialize_case(case_result) -> dict[str, object]:
    return {
        "case_id": case_result.case_id,
        "coding_opportunities": [
            {
                "type": item.coding_issue_type,
                "reason": item.risk_reason,
                "evidence_ids": list(item.evidence_citation_ids),
            }
            for item in case_result.coding_opportunities
        ],
        "ar_flags": [
            {
                "flag_id": item.flag_id,
                "flag_type": item.flag_type,
                "payer": item.payer,
                "balance": str(item.balance),
                "next_deadline": item.next_deadline,
            }
            for item in case_result.ar_flags
        ],
        "denial_opportunities": [
            {
                "denial_id": item.denial_id,
                "category": item.denial_category,
                "payer": item.payer,
                "claim_id": item.claim_id,
            }
            for item in case_result.denial_opportunities
        ],
        "work_queue": [
            {
                "work_item_id": item.work_item_id,
                "priority_band": item.priority_band,
                "payer": item.payer,
                "owner_role": item.owner_role,
                "queue_type": item.queue_type,
                "amount_at_risk": str(item.balance),
                "aging_bucket": item.aging_bucket,
            }
            for item in case_result.work_queue
        ],
    }


def _li(items: Iterable[str]) -> str:
    rendered = "".join(f"<li>{escape(item)}</li>" for item in items)
    return rendered or "<li>None</li>"


def _landing_page() -> str:
    result = _load_result()
    top_case = max(
        result.cases,
        key=lambda item: (
            len(item.work_queue),
            len(item.denial_opportunities),
            len(item.ar_flags),
            len(item.coding_opportunities),
        ),
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citron Health</title>
  <style>
    :root {{
      --bg: #f6efe4;
      --ink: #17222f;
      --muted: #586779;
      --panel: rgba(255, 252, 246, 0.92);
      --line: rgba(23, 34, 47, 0.12);
      --accent: #0f766e;
      --accent-2: #d97706;
      --shadow: 0 24px 80px rgba(23, 34, 47, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at 0% 0%, rgba(15, 118, 110, 0.14), transparent 26rem),
        radial-gradient(circle at 100% 20%, rgba(217, 119, 6, 0.10), transparent 24rem),
        linear-gradient(180deg, #fcf8f1 0%, var(--bg) 100%);
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px 18px 48px; }}
    .hero, .band, .proof {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
    }}
    .hero {{
      padding: 28px;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 20px;
    }}
    .eyebrow {{
      display: inline-block;
      font-size: 0.88rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 14px;
    }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    h1 {{ font-size: clamp(2.4rem, 5vw, 4.8rem); line-height: 0.95; }}
    p {{ margin: 0 0 12px; line-height: 1.55; color: var(--muted); }}
    .cta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 20px;
    }}
    .button {{
      display: inline-block;
      text-decoration: none;
      padding: 12px 18px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--ink);
      background: #fffdf8;
      font-weight: 600;
    }}
    .button.primary {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}
    .hero-card {{
      padding: 18px;
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(244,250,249,0.88));
      border: 1px solid rgba(15, 118, 110, 0.14);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 14px;
      margin-top: 18px;
    }}
    .metric {{
      padding: 16px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.74);
    }}
    .metric strong {{
      display: block;
      font-size: 2rem;
      color: var(--ink);
    }}
    .band {{
      margin-top: 18px;
      padding: 22px;
    }}
    .steps {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }}
    .step {{
      padding: 16px;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.72);
    }}
    .proof {{
      margin-top: 18px;
      padding: 22px;
    }}
    code {{
      font-family: "SFMono-Regular", Menlo, monospace;
      font-size: 0.92em;
      background: rgba(23, 34, 47, 0.06);
      border-radius: 6px;
      padding: 2px 6px;
    }}
    @media (max-width: 900px) {{
      .hero {{ grid-template-columns: 1fr; }}
      main {{ padding: 18px 14px 32px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <span class="eyebrow">Citron Health Demo</span>
        <h1>Revenue integrity review without the black box.</h1>
        <p>Citron Health surfaces deterministic coding, A/R, denial, workflow, and payer-friction signals from a synthetic ambulatory surgery center dataset. Every flagged item is cited, reviewer-safe, and clearly marked for human review.</p>
        <p>The live demo is a browser-based workbench built for fast walkthroughs, not a static brochure. The domain root now sends visitors to a landing page that explains the product and links directly into the working demo.</p>
        <div class="cta-row">
          <a class="button primary" href="/demo">Open Working Demo</a>
          <a class="button" href="/api/summary">View JSON Summary</a>
          <a class="button" href="/demo?case_id={escape(top_case.case_id)}">Open Highest-Signal Case</a>
        </div>
      </div>
      <div class="hero-card">
        <h2>What the demo shows</h2>
        <p><strong>Case review.</strong> Coding opportunities, denial drivers, A/R follow-up, and workflow routing for each synthetic case.</p>
        <p><strong>Manager view.</strong> Queue metrics, urgent work counts, and payer friction signals for quick prioritization.</p>
        <p><strong>Copilot outputs.</strong> Draft follow-up notes, appeal text, workflow guidance, and cited reviewer packets.</p>
        <div class="grid">
          <div class="metric"><strong>{len(result.cases)}</strong>Cases</div>
          <div class="metric"><strong>{sum(len(case.work_queue) for case in result.cases)}</strong>Work Items</div>
          <div class="metric"><strong>{escape(str(result.manager_metrics.get("urgent_items", 0)))}</strong>Urgent</div>
        </div>
      </div>
    </section>

    <section class="band">
      <h2>How to use it</h2>
      <div class="steps">
        <div class="step">
          <h3>1. Start at <code>/demo</code></h3>
          <p>Use the demo workbench to switch between cases and inspect the queue, appeal draft, and workflow guidance.</p>
        </div>
        <div class="step">
          <h3>2. Jump to a case</h3>
          <p>Pass <code>?case_id=ASC-CASE-008</code> to open a specific example with high-value A/R follow-up.</p>
        </div>
        <div class="step">
          <h3>3. Use the APIs</h3>
          <p><code>/api/summary</code>, <code>/api/case</code>, and <code>/health</code> are exposed for integration and quick verification.</p>
        </div>
      </div>
    </section>

    <section class="proof">
      <h2>Safety constraints</h2>
      <p>Synthetic data only. No PHI. No external APIs. No autonomous coding, billing, or payer submission. Every recommendation requires human review.</p>
    </section>
  </main>
</body>
</html>
"""


def _demo_page(selected_case_id: str | None = None) -> str:
    result = _load_result()
    selected = _selected_case(selected_case_id)
    ar = ARCopilot()
    denial = DenialCopilot()
    assistant = WorkflowAssistant()
    intelligence = PayerIntelligenceCopilot()

    ar_note = (
        ar.generate_internal_followup_note(selected.ar_flags[0]).content
        if selected.ar_flags
        else "No A/R flags for the selected synthetic case."
    )
    denial_note = (
        denial.appeal_letter_draft(selected.denial_opportunities[0]).content
        if selected.denial_opportunities
        else "No denial opportunities for the selected synthetic case."
    )
    workflow_note = (
        assistant.generate_role_specific_note(selected.workflow_items[0], role=selected.workflow_items[0].owner_role).content
        if selected.workflow_items
        else "No workflow items for the selected synthetic case."
    )
    intelligence_note = intelligence.answer(
        "Which work items should a manager review today?",
        result.payer_intelligence,
    ).response_text

    case_nav = "".join(
        (
            f"<a class='case-pill{' active' if case.case_id == selected.case_id else ''}' "
            f"href='/?case_id={escape(case.case_id)}'>{escape(case.case_id)}</a>"
        )
        for case in result.cases
    )
    work_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(item.work_item_id)}</td>"
            f"<td>{escape(item.priority_band)}</td>"
            f"<td>{escape(item.payer)}</td>"
            f"<td>{escape(item.owner_role)}</td>"
            f"<td>{escape(item.queue_type)}</td>"
            f"<td>{escape(str(item.balance))}</td>"
            f"<td>{escape(item.aging_bucket)}</td>"
            "</tr>"
        )
        for item in selected.work_queue
    ) or "<tr><td colspan='7'>No queued work items.</td></tr>"

    metrics = result.manager_metrics
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citron Health Demo</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: rgba(255, 251, 245, 0.94);
      --ink: #1b2430;
      --muted: #5a6776;
      --accent: #0f766e;
      --accent-soft: #d7f0eb;
      --border: rgba(27, 36, 48, 0.12);
      --shadow: 0 18px 60px rgba(27, 36, 48, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.12), transparent 28rem),
        linear-gradient(180deg, #fbf7f1 0%, var(--bg) 100%);
    }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }}
    .hero {{
      background: linear-gradient(135deg, rgba(15,118,110,0.14), rgba(255,255,255,0.75));
      border: 1px solid var(--border);
      border-radius: 28px;
      box-shadow: var(--shadow);
      padding: 28px;
    }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    p {{ margin: 0 0 12px; line-height: 1.55; }}
    .warning {{
      display: inline-block;
      padding: 8px 12px;
      border-radius: 999px;
      background: #fff7d6;
      border: 1px solid rgba(137, 94, 0, 0.18);
      color: #704f00;
      font-size: 0.92rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}
    .metric {{
      font-size: 2rem;
      margin-top: 4px;
    }}
    .muted {{ color: var(--muted); }}
    .case-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .case-pill {{
      text-decoration: none;
      color: var(--ink);
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--border);
      padding: 10px 14px;
      border-radius: 999px;
    }}
    .case-pill.active {{
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }}
    .two-col {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 18px;
      margin-top: 18px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 0.95rem;
    }}
    th, td {{
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    ul {{ margin: 0; padding-left: 20px; }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      font-family: "SFMono-Regular", Menlo, monospace;
      font-size: 0.84rem;
      color: #153042;
      background: #f7fbfc;
      border-radius: 16px;
      padding: 14px;
      border: 1px solid rgba(15, 118, 110, 0.12);
    }}
    .api-links a {{
      color: var(--accent);
      text-decoration: none;
      margin-right: 12px;
    }}
    @media (max-width: 900px) {{
      .two-col {{ grid-template-columns: 1fr; }}
      main {{ padding: 20px 14px 32px; }}
      .hero, .card {{ border-radius: 20px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="warning">Synthetic data only. Human review required. No external APIs.</span>
      <h1>Citron Health Demo</h1>
      <p>Interactive workbench for the deterministic ASC revenue-cycle prototype. Use the links below to move between cases, inspect the queue, and review cited copilot outputs.</p>
      <p class="muted">As-of date: {escape(DEFAULT_AS_OF_DATE)}</p>
      <p><a class="case-pill" href="/">Back to Landing Page</a></p>
      <div class="case-nav">{case_nav}</div>
    </section>

    <section class="grid">
      <article class="card">
        <div class="muted">Cases</div>
        <div class="metric">{len(result.cases)}</div>
      </article>
      <article class="card">
        <div class="muted">Work Items</div>
        <div class="metric">{sum(len(case.work_queue) for case in result.cases)}</div>
      </article>
      <article class="card">
        <div class="muted">Urgent Items</div>
        <div class="metric">{escape(str(metrics.get("urgent_items", 0)))}</div>
      </article>
      <article class="card">
        <div class="muted">Top Payer Friction</div>
        <div class="metric">{escape(next(iter(result.payer_intelligence.payer_friction_score), "n/a"))}</div>
      </article>
    </section>

    <section class="two-col">
      <article class="card">
        <h2>Selected Case: {escape(selected.case_id)}</h2>
        <p class="muted">Coding opportunities, A/R flags, and denial opportunities are rendered from the deterministic pipeline.</p>
        <h3>Coding</h3>
        <ul>{_li(f"{item.coding_issue_type}: {item.risk_reason}" for item in selected.coding_opportunities)}</ul>
        <h3>A/R Flags</h3>
        <ul>{_li(f"{item.flag_type} | {item.payer} | {item.balance}" for item in selected.ar_flags)}</ul>
        <h3>Denials</h3>
        <ul>{_li(f"{item.denial_category}: {item.claim_id}" for item in selected.denial_opportunities)}</ul>
      </article>

      <article class="card">
        <h2>Manager Signals</h2>
        <pre>{escape(json.dumps(metrics, indent=2, sort_keys=True))}</pre>
        <h3 style="margin-top:16px;">API</h3>
        <p class="api-links">
          <a href="/api/summary">/api/summary</a>
          <a href="/api/case?case_id={escape(selected.case_id)}">/api/case</a>
          <a href="/health">/health</a>
        </p>
      </article>
    </section>

    <section class="card" style="margin-top:18px;">
      <h2>Work Queue</h2>
      <table>
        <thead>
          <tr>
            <th>Work Item</th>
            <th>Priority</th>
            <th>Payer</th>
            <th>Owner</th>
            <th>Queue</th>
            <th>Amount at Risk</th>
            <th>Aging</th>
          </tr>
        </thead>
        <tbody>{work_rows}</tbody>
      </table>
    </section>

    <section class="two-col">
      <article class="card">
        <h2>A/R Copilot</h2>
        <pre>{escape(ar_note)}</pre>
        <h2 style="margin-top:16px;">Denial Appeal Copilot</h2>
        <pre>{escape(denial_note)}</pre>
      </article>

      <article class="card">
        <h2>Workflow Assistant</h2>
        <pre>{escape(workflow_note)}</pre>
        <h2 style="margin-top:16px;">Payer Intelligence</h2>
        <pre>{escape(intelligence_note)}</pre>
      </article>
    </section>
  </main>
</body>
</html>
"""


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    query = parse_qs(environ.get("QUERY_STRING", ""))
    result = _load_result()

    if path == "/health":
        return _json_response(start_response, {"ok": True, "as_of_date": DEFAULT_AS_OF_DATE})

    if path == "/api/summary":
        return _json_response(
            start_response,
            {
                "as_of_date": DEFAULT_AS_OF_DATE,
                "manager_metrics": result.manager_metrics,
                "payer_friction_score": result.payer_intelligence.payer_friction_score,
                "cases": [item.case_id for item in result.cases],
            },
        )

    if path == "/api/case":
        case_id = query.get("case_id", [None])[0]
        if not case_id:
            return _json_response(start_response, {"error": "case_id query parameter is required"}, "400 Bad Request")
        for item in result.cases:
            if item.case_id == case_id:
                return _json_response(start_response, _serialize_case(item))
        return _json_response(start_response, {"error": f"unknown case_id: {case_id}"}, "404 Not Found")

    if path == "/" or path == "":
        return _html_response(start_response, _landing_page())

    if path == "/demo":
        selected = query.get("case_id", [None])[0]
        if selected and all(case.case_id != selected for case in result.cases):
            return _html_response(start_response, _demo_page(), "404 Not Found")
        return _html_response(start_response, _demo_page(selected))

    return _json_response(start_response, {"error": "not found"}, "404 Not Found")
