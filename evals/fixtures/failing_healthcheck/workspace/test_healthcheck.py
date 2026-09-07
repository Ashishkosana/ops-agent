from healthcheck import url


def test_health_path() -> None:
    assert url("http://svc") == "http://svc/health"
    assert url("http://svc/") == "http://svc/health"
