"""FastAPI integration test for hub endpoints using an in-memory SQLite DB."""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.auth import get_current_user, get_db
from app.models import Base
from app.models.hub import Hub
from app.models.user import UserRole, User
from app.models.hub_membership import HubMembership


# In-memory SQLite for lightweight API validation
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def override_get_db():
    db = TestingSessionLocal()
    Base.metadata.create_all(bind=engine, tables=[Hub.__table__, User.__table__, HubMembership.__table__])
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    class DummyUser:
        id = uuid.uuid4()
        role = UserRole.admin
        is_active = True

    return DummyUser()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


def test_hub_create_update_and_user_flow():
    create_payload = {
        "name": "Test Hub",
        "code": "HUB-TEST-01",
        "tier": "Individual",
        "payment_method": "manual_invoice",
        "billing_cycle": "monthly",
        "primary_contact_name": "Admin User",
        "primary_contact_email": "admin@example.com",
        "country": "Zimbabwe",
        "city": "Harare",
    }

    create_response = client.post("/api/v1/hubs", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    hub = create_response.json()
    assert hub["code"].startswith("HUB-TEST"), hub
    assert hub["tier"].lower() == "individual"
    hub_id = hub["id"]

    patch_response = client.patch(
        f"/api/v1/hubs/{hub_id}",
        json={"tier": "Business", "status": "provisioning", "billing_cycle": "annual"},
    )
    assert patch_response.status_code == 200, patch_response.text
    patched = patch_response.json()
    assert patched["tier"].lower() == "business"
    assert patched["billing_cycle"] == "annual"
    assert patched["status"] == "provisioning"

    user_response = client.post(
        f"/api/v1/hubs/{hub_id}/users",
        json={"name": "Operator", "email": "operator@example.com", "role": "client"},
    )
    assert user_response.status_code == 200, user_response.text
    user_payload = user_response.json()
    assert user_payload["email"] == "operator@example.com"

    list_response = client.get("/api/v1/hubs")
    assert list_response.status_code == 200
    hubs = list_response.json()
    assert isinstance(hubs, list)
    assert any(item["id"] == hub_id for item in hubs)
