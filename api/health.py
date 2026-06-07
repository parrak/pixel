from app import DEFAULT_AS_OF_DATE, _json_response


def app(environ, start_response):
    return _json_response(start_response, {"ok": True, "as_of_date": DEFAULT_AS_OF_DATE})
