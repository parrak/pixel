import json

from app import app


def _request(path: str, query_string: str = ""):
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(
        app(
            {
                "PATH_INFO": path,
                "QUERY_STRING": query_string,
            },
            start_response,
        )
    )
    captured["body"] = body
    return captured


def test_root_page_renders_html():
    response = _request("/")

    assert response["status"] == "200 OK"
    assert response["headers"]["Content-Type"].startswith("text/html")
    assert b"HoldCo Command Center" in response["body"]
    assert b"Open HoldCo Demo" in response["body"]


def test_demo_page_renders_html():
    response = _request("/demo")

    assert response["status"] == "200 OK"
    assert response["headers"]["Content-Type"].startswith("text/html")
    assert b"Workflow System of Record inside Citron" in response["body"]
    assert b"Revenue at risk" in response["body"]
    assert b"Transaction lifecycle graph" in response["body"]


def test_case_api_requires_case_id():
    response = _request("/api/case")

    assert response["status"] == "400 Bad Request"
    payload = json.loads(response["body"])
    assert "case_id" in payload["error"]


def test_case_api_returns_case_payload():
    response = _request("/api/case", "case_id=ASC-CASE-008")

    assert response["status"] == "200 OK"
    payload = json.loads(response["body"])
    assert payload["case_id"] == "ASC-CASE-008"
    assert payload["operational_tasks"]


def test_holdco_api_returns_phase_four_payload():
    response = _request("/api/holdco")

    assert response["status"] == "200 OK"
    payload = json.loads(response["body"])
    assert payload["holdco"]["holdco_id"] == "holdco_citron"
    assert payload["holdco_dashboard"]["portfolio_ebitda"]
    assert payload["value_creation_initiatives"]


def test_acquisition_api_returns_integration_plan():
    response = _request("/api/acquisition", "specialty=Cardiology&headcount=90&workflow_maturity=fragmented")

    assert response["status"] == "200 OK"
    payload = json.loads(response["body"])
    assert payload["specialty"] == "Cardiology"
    assert payload["ninety_day_roadmap"]
    assert payload["value_creation_opportunities"]
