import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app


# We use session scope for the client so the lifespan (and disposal)
# only happens ONCE at the very end of all tests.
@pytest.fixture(scope="session")
async def client():
    # Use the ASGITransport which triggers your lifespan
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_managers(client: AsyncClient) -> None:
    response = await client.get("/trials/managers")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_trials_crud(client: AsyncClient) -> None:
    # 1. Create
    payload = {
        "source": "Google",
        "student_id": "649073",
        "student_name": "測試王",
        "middle_school_name": "string",
        "middle_school_class": "string",
        "high_school_name": "string",
        "high_school_class": "string",
        "registered_class": "string",
        "trial_date": "2026-03-23",
        "telephone": "0912345678",  # Use realistic numbers
        "mobile": "0912345678",
        "notes": "",
        "parent_name": "string",
        "manager": "string",
        "status": "string",
        "current_grade": "string",
    }

    create_resp = await client.post("/trials/", json=payload)

    if create_resp.status_code != 200:
        print(f"\nCREATE FAILED: {create_resp.status_code} - {create_resp.text}")

    assert create_resp.status_code == status.HTTP_200_OK
    data = create_resp.json()
    trial_id = data["id"]

    # 2. Read One
    read_resp = await client.get(f"/trials/{trial_id}")
    assert read_resp.status_code == status.HTTP_200_OK
    assert read_resp.json()["student_name"] == "測試王"

    # 3. Update
    payload["student_name"] = "測試男"
    update_resp = await client.put(f"/trials/{trial_id}", json=payload)
    assert update_resp.status_code == status.HTTP_200_OK
    assert update_resp.json()["student_name"] == "測試男"

    # 4. Delete
    del_resp = await client.delete(f"/trials/{trial_id}")
    assert del_resp.status_code == status.HTTP_200_OK

    # 5. Verify Delete
    verify_resp = await client.get(f"/trials/{trial_id}")
    assert verify_resp.status_code == status.HTTP_404_NOT_FOUND
