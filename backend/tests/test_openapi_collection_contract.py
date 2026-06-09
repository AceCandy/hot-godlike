from fastapi.testclient import TestClient

from app.main import create_app


def test_openapi_includes_m2_collection_paths() -> None:
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    expected_methods = {
        "/api/sources": {"get", "post"},
        "/api/sources/{source_id}": {"get", "patch"},
        "/api/sources/{source_id}/enable": {"post"},
        "/api/sources/{source_id}/disable": {"post"},
        "/api/sources/preview": {"post"},
        "/api/sources/{source_id}/fetch": {"post"},
        "/api/fetch-runs": {"get"},
        "/api/fetch-runs/{run_id}": {"get"},
        "/api/raw-items": {"get"},
        "/api/raw-items/{raw_item_id}": {"get"},
        "/api/source-health": {"get"},
    }

    for path, methods in expected_methods.items():
        assert path in paths
        assert methods.issubset(paths[path])
