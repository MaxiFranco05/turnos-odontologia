# Test: C-06 — appointment request endpoint
## Test layer: Unit / Integration
## Description: Test the POST /turnos/solicitar endpoint for creating appointment requests with overlap validation

"""C-06 appointment-request: FastAPI endpoint for patient appointment requests"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from decimal import Decimal

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from app.core.main import app
    return TestClient(app)


def test_appointment_request_valid(test_client):
    """Test: Valid appointment request should be accepted (Scenario 1 from specs)."""
    # Given: Dentist has no turnos for the requested date
    # When: Patient requests a non-overlapping slot
    # Then: Turno is accepted with status "confirmed"
    response = test_client.post(
        "/turnos/solicitar",
        json={
            "patient_id": "patient-001",
            "dentist_id": "dentist-001",
            "date": "2026-05-15",
            "time": "11:30",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["patient_id"] == "patient-001"
    assert data["dentist_id"] == "dentist-001"
    assert data["date"] == "2026-05-15"
    assert data["time"] == "11:30"


def test_appointment_request_overlap_partial(test_client):
    """Test: Partial overlap should be rejected (Scenario 2 from specs)."""
    # First, create an existing turno for the dentist
    # Given: Dentist has turno [10:00-11:00] on 2026-05-15
    # When: Patient requests [10:30-11:30] (overlaps with existing)
    # Then: Turno is rejected with 422 error and overlap reason
    response = test_client.post(
        "/turnos/solicitar",
        json={
            "patient_id": "patient-002",
            "dentist_id": "dentist-001",
            "date": "2026-05-15",
            "time": "10:30",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "rejected"
    assert "overlap" in data["reason"].lower() or "already has" in data["reason"].lower()


def test_appointment_request_overlap_contained(test_client):
    """Test: Contained turno should be rejected (Scenario 3 from specs)."""
    # Given: Dentist has turno [10:00-11:00] on 2026-05-15
    # When: Patient requests [09:00-11:30] (contains the existing turno)
    # Then: Turno is rejected with 422 error and contained overlap reason
    response = test_client.post(
        "/turnos/solicitar",
        json={
            "patient_id": "patient-003",
            "dentist_id": "dentist-001",
            "date": "2026-05-15",
            "time": "09:30",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "rejected"
    assert "overlap" in data["reason"].lower() or "already has" in data["reason"].lower()