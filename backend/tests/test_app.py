"""
Unit tests for the Luxury Car Resale Showroom API.
Run with:  pytest app/tests/ -v
"""

import json
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as flask_app   # noqa: E402
import app as app_module           # noqa: E402


# ════════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def reset_cars():
    """Re-seed the cars store before every test for full isolation."""
    app_module.cars.clear()
    app_module._seed_cars()
    yield
    app_module.cars.clear()


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _post_car(client, **overrides):
    """Helper — create a minimal valid car and return the parsed JSON response."""
    payload = {
        "brand": "Porsche",
        "model": "Cayenne Coupé",
        "year": 2023,
        "price": 125000,
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "color": "Jet Black",
        "mileage": 4500,
        "engine": "3.0L V6 Turbo",
        "power_hp": 340,
    }
    payload.update(overrides)
    return client.post(
        "/api/cars",
        data=json.dumps(payload),
        content_type="application/json",
    )


# ════════════════════════════════════════════════════════════════════════════
# 1. Health check
# ════════════════════════════════════════════════════════════════════════════

def test_health_returns_200(client):
    """GET /health must return 200 with status 'healthy'."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


# ════════════════════════════════════════════════════════════════════════════
# 2. Info endpoint
# ════════════════════════════════════════════════════════════════════════════

def test_info_endpoint(client):
    """GET /info must return app metadata including total_cars."""
    resp = client.get("/info")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "app" in data
    assert "total_cars" in data
    assert data["total_cars"] == 9   # 9 seeded cars


# ════════════════════════════════════════════════════════════════════════════
# 3. List cars
# ════════════════════════════════════════════════════════════════════════════

def test_get_all_cars_returns_seeded_data(client):
    """GET /api/cars must return all 9 seeded luxury cars."""
    resp = client.get("/api/cars")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 9


def test_filter_cars_by_brand(client):
    """GET /api/cars?brand=Ferrari must return only Ferrari cars."""
    resp = client.get("/api/cars?brand=Ferrari")
    assert resp.status_code == 200
    cars = resp.get_json()
    assert len(cars) >= 1
    assert all(c["brand"] == "Ferrari" for c in cars)


def test_filter_cars_by_max_price(client):
    """GET /api/cars?max_price=200000 must return only cars ≤ $200,000."""
    resp = client.get("/api/cars?max_price=200000")
    assert resp.status_code == 200
    cars = resp.get_json()
    assert all(c["price"] <= 200000 for c in cars)


def test_filter_cars_by_fuel_type(client):
    """GET /api/cars?fuel_type=Petrol must return only petrol cars."""
    resp = client.get("/api/cars?fuel_type=Petrol")
    assert resp.status_code == 200
    cars = resp.get_json()
    assert len(cars) > 0
    assert all(c["fuel_type"] == "Petrol" for c in cars)


def test_search_cars_by_model_keyword(client):
    """GET /api/cars?search=ghost must find the Rolls-Royce Ghost."""
    resp = client.get("/api/cars?search=ghost")
    assert resp.status_code == 200
    cars = resp.get_json()
    assert len(cars) >= 1
    assert any("Ghost" in c["model"] for c in cars)


# ════════════════════════════════════════════════════════════════════════════
# 4. Get single car
# ════════════════════════════════════════════════════════════════════════════

def test_get_single_car(client):
    """GET /api/cars/car-001 must return the Lamborghini Huracán."""
    resp = client.get("/api/cars/car-001")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["brand"] == "Lamborghini"
    assert data["id"] == "car-001"


def test_get_nonexistent_car_returns_404(client):
    """GET /api/cars/<bad-id> must return 404."""
    resp = client.get("/api/cars/does-not-exist")
    assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════════════════
# 5. Create car
# ════════════════════════════════════════════════════════════════════════════

def test_create_car_returns_201(client):
    """POST /api/cars with valid payload must return 201 with car data."""
    resp = _post_car(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["brand"] == "Porsche"
    assert data["model"] == "Cayenne Coupé"
    assert data["available"] is True
    assert data["sold"] is False
    assert "id" in data
    assert "created_at" in data


def test_create_car_missing_fields_returns_400(client):
    """POST /api/cars missing required fields must return 400."""
    resp = client.post(
        "/api/cars",
        data=json.dumps({"brand": "Porsche"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_create_car_appears_in_listing(client):
    """A newly created car must be returned by GET /api/cars."""
    _post_car(client, model="Taycan Turbo S")
    resp = client.get("/api/cars")
    models = [c["model"] for c in resp.get_json()]
    assert "Taycan Turbo S" in models


# ════════════════════════════════════════════════════════════════════════════
# 6. Update car
# ════════════════════════════════════════════════════════════════════════════

def test_update_car_price(client):
    """PUT /api/cars/<id> must update the car price."""
    resp = client.put(
        "/api/cars/car-001",
        data=json.dumps({"price": 270000}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["price"] == 270000


def test_update_car_availability(client):
    """PUT /api/cars/<id> can toggle availability."""
    resp = client.put(
        "/api/cars/car-002",
        data=json.dumps({"available": False}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["available"] is False


def test_update_nonexistent_car_returns_404(client):
    """PUT /api/cars/<bad-id> must return 404."""
    resp = client.put(
        "/api/cars/ghost-id",
        data=json.dumps({"price": 100000}),
        content_type="application/json",
    )
    assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════════════════
# 7. Delete car
# ════════════════════════════════════════════════════════════════════════════

def test_delete_car(client):
    """DELETE /api/cars/<id> must remove the car and return 200."""
    resp = client.delete("/api/cars/car-003")
    assert resp.status_code == 200

    get_resp = client.get("/api/cars/car-003")
    assert get_resp.status_code == 404


def test_delete_nonexistent_car_returns_404(client):
    """DELETE /api/cars/<bad-id> must return 404."""
    resp = client.delete("/api/cars/phantom-id")
    assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════════════════
# 8. Purchase — PayPal proxy error handling
# ════════════════════════════════════════════════════════════════════════════

def test_purchase_car_service_unavailable(client, monkeypatch):
    """POST /api/cars/<id>/purchase must return 503 when PayPal service is down."""
    import requests as req

    def mock_post(*args, **kwargs):
        raise req.exceptions.ConnectionError("Payment service is down")

    monkeypatch.setattr(req, "post", mock_post)

    resp = client.post(
        "/api/cars/car-004/purchase",
        data=json.dumps({"buyer_name": "John Doe", "buyer_email": "john@example.com"}),
        content_type="application/json",
    )
    assert resp.status_code == 503
    assert "error" in resp.get_json()


def test_purchase_already_sold_car_returns_409(client):
    """POST /api/cars/<id>/purchase on a sold car must return 409."""
    app_module.cars["car-001"]["sold"]      = True
    app_module.cars["car-001"]["available"] = False

    resp = client.post(
        "/api/cars/car-001/purchase",
        data=json.dumps({"buyer_email": "buyer@example.com"}),
        content_type="application/json",
    )
    assert resp.status_code == 409


def test_purchase_unavailable_car_returns_409(client):
    """POST /api/cars/<id>/purchase on an unavailable car must return 409."""
    app_module.cars["car-002"]["available"] = False

    resp = client.post(
        "/api/cars/car-002/purchase",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 409


# ════════════════════════════════════════════════════════════════════════════
# 9. HTML routes
# ════════════════════════════════════════════════════════════════════════════

def test_index_page_returns_200(client):
    """GET / must render the showroom HTML page."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Luxury" in resp.data or b"luxury" in resp.data


def test_car_detail_page_returns_200(client):
    """GET /car/<id> must render the car detail HTML page."""
    resp = client.get("/car/car-001")
    assert resp.status_code == 200
    assert b"Lamborghini" in resp.data


def test_car_detail_page_404(client):
    """GET /car/<bad-id> must return 404."""
    resp = client.get("/car/nonexistent-car")
    assert resp.status_code == 404
