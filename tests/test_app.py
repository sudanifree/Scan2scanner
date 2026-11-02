from app import app


def test_homepage_is_served():
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data


def test_scanners_api_returns_discovered_devices(monkeypatch):
    monkeypatch.setattr(
        "app.list_scanners",
        lambda: ([{"id": "test:scanner", "name": "Test scanner"}], None),
    )

    response = app.test_client().get("/api/scanners")

    assert response.status_code == 200
    assert response.get_json() == {
        "scanners": [{"id": "test:scanner", "name": "Test scanner"}]
    }