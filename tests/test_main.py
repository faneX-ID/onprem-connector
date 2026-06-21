"""
Basic tests for the OnPrem Connector.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "faneX-ID OnPrem Connector" in data["service"]


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "connector_name" in data


def test_status_endpoint():
    """Test status endpoint."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "connector" in data
    assert "cloud" in data
    assert "network" in data


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "fanexid_connector" in response.text
