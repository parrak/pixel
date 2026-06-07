from app import _html_response, _landing_page


def app(environ, start_response):
    return _html_response(start_response, _landing_page())
