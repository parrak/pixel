from urllib.parse import parse_qs

from app import _demo_page, _html_response, _load_result


def app(environ, start_response):
    query = parse_qs(environ.get("QUERY_STRING", ""))
    selected = query.get("case_id", [None])[0]
    result = _load_result()
    if selected and all(case.case_id != selected for case in result.cases):
        return _html_response(start_response, _demo_page(), "404 Not Found")
    return _html_response(start_response, _demo_page(selected))
