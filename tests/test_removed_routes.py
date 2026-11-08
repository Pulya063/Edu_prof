import pytest


@pytest.mark.parametrize("route,method", [
    ("/api/roi/analyze", "POST"),
    ("/api/roi/trash", "GET"),
    ("/api/roi/1", "DELETE"),
    ("/api/roi/1/restore", "POST"),
    # Removed in v3.0 cleanup: US-dataset trial, history, US university search, HTML pages, resource audit.
    ("/api/roi/trial", "POST"),
    ("/api/roi/history", "GET"),
    ("/api/roi/universities/search", "GET"),
    ("/api/roi/universities/tuition", "GET"),
    ("/ui/", "GET"),
    ("/ui/login", "GET"),
    ("/resources", "GET"),
    ("/api/resources", "GET"),
    ("/roadmap/", "GET"),
    ("/roadmap/generate", "POST"),
])
def test_removed_legacy_routes(client, route, method):
    assert client.open(route, method=method).status_code == 404
