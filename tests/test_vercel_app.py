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
    assert b"Citron Health Demo" in response["body"]
    assert b"Open Working Demo" in response["body"]


def test_demo_page_renders_html():
    response = _request("/demo")

    assert response["status"] == "200 OK"
    assert response["headers"]["Content-Type"].startswith("text/html")
    assert b"Back to Landing Page" in response["body"]


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
    assert payload["work_queue"]
