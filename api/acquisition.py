from urllib.parse import parse_qs

from app import _json_response
from asc_rcm_lite.operations import simulate_acquisition


def app(environ, start_response):
    query = parse_qs(environ.get("QUERY_STRING", ""))
    specialty = query.get("specialty", ["ASC"])[0]
    headcount = int(query.get("headcount", ["75"])[0])
    maturity = query.get("workflow_maturity", ["developing"])[0]
    systems = tuple(query.get("systems", ["EHR", "Practice Management", "Clearinghouse", "Payer Portals", "Spreadsheets"]))
    return _json_response(
        start_response,
        simulate_acquisition(
            specialty=specialty,
            headcount=headcount,
            workflow_maturity=maturity,
            systems=systems,
        ),
    )
