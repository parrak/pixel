from urllib.parse import parse_qs

from app import _json_response, _load_result, _serialize_case


def app(environ, start_response):
    case_id = parse_qs(environ.get("QUERY_STRING", "")).get("case_id", [None])[0]
    if not case_id:
        return _json_response(start_response, {"error": "case_id query parameter is required"}, "400 Bad Request")

    result = _load_result()
    for item in result.cases:
        if item.case_id == case_id:
            return _json_response(start_response, _serialize_case(item))
    return _json_response(start_response, {"error": f"unknown case_id: {case_id}"}, "404 Not Found")
