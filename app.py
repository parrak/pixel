from __future__ import annotations

import json
from functools import lru_cache
from html import escape
from urllib.parse import parse_qs

from asc_rcm_lite.operations import simulate_acquisition
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
    return next((case for case in result.cases if case.operational_tasks), result.cases[0])


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
        "operational_tasks": [
            {
                "task_id": task.task_id,
                "organization": task.organization_name,
                "facility": task.facility_name,
                "team": task.team_name,
                "assignee": task.assignee_name,
                "workflow": task.workflow_name,
                "priority": task.priority_band,
                "amount_at_risk": str(task.amount_at_risk),
                "recommendation": task.recommendations[0].title,
                "history": [
                    {
                        "decision": record.decision.decision,
                        "actor": record.decision.actor_name,
                        "outcome": record.outcome.status,
                        "financial_result": str(record.outcome.financial_result),
                        "resolution_time_hours": record.outcome.resolution_time_hours,
                    }
                    for record in task.history
                ],
            }
            for task in case_result.operational_tasks
        ],
    }


def _landing_page() -> str:
    result = _load_result()
    portfolio = result.portfolio_snapshot
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citron Health Operator OS</title>
  <style>
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: #17222f;
      background:
        radial-gradient(circle at 0% 0%, rgba(15, 118, 110, 0.14), transparent 26rem),
        radial-gradient(circle at 100% 20%, rgba(217, 119, 6, 0.10), transparent 24rem),
        linear-gradient(180deg, #fcf8f1 0%, #f6efe4 100%);
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px 18px 48px; }}
    .hero, .panel {{
      background: rgba(255, 252, 246, 0.92);
      border: 1px solid rgba(23, 34, 47, 0.12);
      border-radius: 28px;
      box-shadow: 0 24px 80px rgba(23, 34, 47, 0.10);
      padding: 28px;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 18px; }}
    .metric {{ padding: 16px; border-radius: 20px; border: 1px solid rgba(23, 34, 47, 0.12); background: rgba(255,255,255,0.76); }}
    .metric strong {{ display: block; font-size: 2rem; }}
    .button {{ display: inline-block; margin-right: 12px; margin-top: 12px; padding: 12px 18px; border-radius: 999px; text-decoration: none; border: 1px solid rgba(23,34,47,0.12); }}
    .primary {{ background: #0f766e; color: white; border-color: #0f766e; }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div style="text-transform:uppercase;letter-spacing:.08em;color:#0f766e;font-size:.88rem;">Citron Health Phase 3</div>
      <h1 style="font-size:clamp(2.4rem,5vw,4.8rem);line-height:.95;margin:.4rem 0 1rem;">Operator Operating System for Specialty Revenue Cycle</h1>
      <p>Citron exists to make acquired specialty RCM businesses better operators. The software sits above EHRs, PM systems, payer portals, and clearinghouses to standardize task ownership, human decision-making, and outcome tracking across a portfolio.</p>
      <p>The product is no longer centered on coding review or denial review. Those remain inside the system as features, while the operating model centers on organization, facility, team, user, workflow, task, recommendation, decision, and outcome.</p>
      <a class="button primary" href="/demo">Open Operator Demo</a>
      <a class="button" href="/api/summary">View Portfolio Summary</a>
    </section>
    <section class="grid">
      <article class="metric"><div>Organizations</div><strong>{len(portfolio["organizations"])}</strong></article>
      <article class="metric"><div>Revenue at risk</div><strong>${escape(portfolio["portfolio_metrics"]["revenue_at_risk"])}</strong></article>
      <article class="metric"><div>Open work</div><strong>{escape(str(portfolio["portfolio_metrics"]["open_work"]))}</strong></article>
      <article class="metric"><div>Recovery pipeline</div><strong>${escape(portfolio["portfolio_metrics"]["recovery_pipeline"])}</strong></article>
    </section>
    <section class="panel" style="margin-top:18px;">
      <h2>What Phase 3 adds</h2>
      <ul>
        <li>Portfolio view for ASC Alpha, ASC Bravo, and ASC Charlie</li>
        <li>Decision memory with financial result and resolution time</li>
        <li>Config-backed workflow definition engine</li>
        <li>Monday morning executive operating narrative</li>
        <li>Acquisition integration simulator</li>
      </ul>
    </section>
  </main>
</body>
</html>
"""


def _demo_page(selected_case_id: str | None = None) -> str:
    result = _load_result()
    portfolio = result.portfolio_snapshot
    monday = portfolio["monday_morning"]
    selected = _selected_case(selected_case_id)
    selected_task = selected.operational_tasks[0]
    role_rows = "".join(
        f"<tr><td>{escape(view['label'])}</td><td>{escape(str(view['queue_size']))}</td><td>${escape(view['revenue_at_risk'])}</td><td>${escape(view['financial_result'])}</td></tr>"
        for view in portfolio["role_views"]
    )
    history_rows = "".join(
        f"<tr><td>{escape(record.decision.actor_name)}</td><td>{escape(record.decision.decision)}</td><td>{escape(record.outcome.status)}</td><td>${escape(str(record.outcome.financial_result))}</td><td>{escape(str(record.outcome.resolution_time_hours))}</td></tr>"
        for record in selected_task.history
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citron Health Operator Demo</title>
  <style>
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: #1b2430;
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.12), transparent 28rem),
        linear-gradient(180deg, #fbf7f1 0%, #f4efe6 100%);
    }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }}
    .hero, .card {{
      background: rgba(255, 251, 245, 0.94);
      border: 1px solid rgba(27, 36, 48, 0.12);
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 18px 60px rgba(27, 36, 48, 0.10);
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 18px; }}
    .two-col {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 18px; margin-top: 18px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid rgba(27, 36, 48, 0.12); vertical-align: top; }}
    .pill {{ display:inline-block;padding:8px 12px;border-radius:999px;background:#fff7d6;border:1px solid rgba(137,94,0,.18);color:#704f00;font-size:.92rem; }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="pill">Synthetic data only. Human review required. No autonomous workflows.</span>
      <h1 style="margin:.75rem 0 1rem;">Monday Morning inside Citron</h1>
      <p>{escape(monday['vp_user']['display_name'])}, {escape(monday['vp_user']['title'])}, opens Citron and sees a portfolio operating system rather than a detector screen.</p>
      <ul>{"".join(f"<li>{escape(line)}</li>" for line in monday["executive_brief"])}</ul>
    </section>
    <section class="grid">
      <article class="card"><div>Revenue at risk</div><h2>${escape(portfolio["portfolio_metrics"]["revenue_at_risk"])}</h2></article>
      <article class="card"><div>Open tasks</div><h2>{escape(str(portfolio["portfolio_metrics"]["open_work"]))}</h2></article>
      <article class="card"><div>Workflow bottlenecks</div><h2>{escape(", ".join(monday["workflow_bottlenecks"]))}</h2></article>
      <article class="card"><div>Critical work</div><h2>{escape(str(len(monday["critical_work"])))}</h2></article>
    </section>
    <section class="two-col">
      <article class="card">
        <h2>Role queues</h2>
        <table>
          <thead><tr><th>Role</th><th>Queue</th><th>Revenue at risk</th><th>Financial result</th></tr></thead>
          <tbody>{role_rows}</tbody>
        </table>
      </article>
      <article class="card">
        <h2>Selected task</h2>
        <p><strong>{escape(selected_task.title)}</strong></p>
        <p>{escape(selected_task.description)}</p>
        <p><strong>Organization:</strong> {escape(selected_task.organization_name or "")}<br>
        <strong>Facility:</strong> {escape(selected_task.facility_name or "")}<br>
        <strong>Assignee:</strong> {escape(selected_task.assignee_name or "")}<br>
        <strong>Recommendation:</strong> {escape(selected_task.recommendations[0].title)}</p>
      </article>
    </section>
    <section class="card" style="margin-top:18px;">
      <h2>Decision memory</h2>
      <table>
        <thead><tr><th>Actor</th><th>Decision</th><th>Outcome</th><th>Financial result</th><th>Resolution hours</th></tr></thead>
        <tbody>{history_rows}</tbody>
      </table>
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
                "operational_metrics": result.operational_metrics,
                "portfolio_snapshot": result.portfolio_snapshot,
                "cases": [item.case_id for item in result.cases],
            },
        )

    if path == "/api/portfolio":
        return _json_response(start_response, result.portfolio_snapshot)

    if path == "/api/case":
        case_id = query.get("case_id", [None])[0]
        if not case_id:
            return _json_response(start_response, {"error": "case_id query parameter is required"}, "400 Bad Request")
        for item in result.cases:
            if item.case_id == case_id:
                return _json_response(start_response, _serialize_case(item))
        return _json_response(start_response, {"error": f"unknown case_id: {case_id}"}, "404 Not Found")

    if path == "/api/acquisition":
        specialty = query.get("specialty", ["ASC"])[0]
        headcount = int(query.get("headcount", ["75"])[0])
        maturity = query.get("workflow_maturity", ["developing"])[0]
        systems = tuple(query.get("systems", ["EHR", "Practice Management", "Clearinghouse", "Payer Portals"]))
        return _json_response(
            start_response,
            simulate_acquisition(
                specialty=specialty,
                headcount=headcount,
                workflow_maturity=maturity,
                systems=systems,
            ),
        )

    if path == "/" or path == "":
        return _html_response(start_response, _landing_page())

    if path == "/demo":
        selected = query.get("case_id", [None])[0]
        return _html_response(start_response, _demo_page(selected))

    return _json_response(start_response, {"error": "not found"}, "404 Not Found")
