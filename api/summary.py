from app import DEFAULT_AS_OF_DATE, _json_response, _load_result


def app(environ, start_response):
    result = _load_result()
    return _json_response(
        start_response,
        {
            "as_of_date": DEFAULT_AS_OF_DATE,
            "manager_metrics": result.manager_metrics,
            "payer_friction_score": result.payer_intelligence.payer_friction_score,
            "cases": [item.case_id for item in result.cases],
        },
    )
