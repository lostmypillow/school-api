import os
from pathlib import Path
import uuid
from dotenv import load_dotenv
import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient
import app.core.exec_sql as exec_sql_module
from app.core.exec_sql import close_db, init_db
from app.main import app


env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


exec_sql_module.DSN = f"postgresql://postgres:{os.getenv("DB_PWD", "")}@{os.getenv("DB_HOST", "localhost")}:5432/student_db"

pytestmark = pytest.mark.asyncio(loop_scope="session")



@pytest_asyncio.fixture(loop_scope="session", scope="session", autouse=True)
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await init_db()
        yield ac
        await close_db()


@pytest.fixture
def unique_tutor_data():
    uid = uuid.uuid4().hex[:8]
    return {
        "id": f"tutor_{uid}",
        "name": f"Test Tutor {uid}",
        "card_id": f"card_{uid}",
        "college": "College of Engineering",
        "new_college": "College of Test",
        "department": "Test Dep",
        "email": f"tutor_{uid}@example.com",
    }


async def test_create_and_get_tutor(client: AsyncClient, unique_tutor_data: dict) -> None:
    create_resp = await client.post(url="/tutor/", json=unique_tutor_data)
    assert create_resp.status_code == status.HTTP_201_CREATED
    assert "detail" in create_resp.json()

    tutor_id = unique_tutor_data["id"]
    get_resp = await client.get(f"/tutor/{tutor_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    data = get_resp.json()
    assert data["id"] == tutor_id
    assert data["name"] == unique_tutor_data["name"]
    assert data["email"] == unique_tutor_data["email"]


async def test_get_all_tutors_pagination(client: AsyncClient) -> None:
    resp = await client.get("/tutor/page/1")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)


async def test_update_tutor(client: AsyncClient, unique_tutor_data: dict) -> None:
    tutor_id = unique_tutor_data["id"]

    create_resp = await client.post(url="/tutor/", json=unique_tutor_data)
    assert create_resp.status_code == status.HTTP_201_CREATED

    update_payload = {
        "id": tutor_id,
        "name": f"Updated {unique_tutor_data['name']}",
        "department": "Test New Department",
    }
    update_resp = await client.put(url="/tutor/", json=update_payload)
    assert update_resp.status_code == status.HTTP_200_OK

    get_resp = await client.get(f"/tutor/{tutor_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["name"] == update_payload["name"]
    assert get_resp.json()["department"] == update_payload["department"]


async def test_delete_tutor(client: AsyncClient, unique_tutor_data: dict) -> None:
    tutor_id = unique_tutor_data["id"]

    create_resp = await client.post(url="/tutor/", json=unique_tutor_data)
    assert create_resp.status_code == status.HTTP_201_CREATED

    delete_resp = await client.request(method="DELETE", url="/tutor/", json={"id": tutor_id})
    assert delete_resp.status_code == status.HTTP_200_OK

    get_resp = await client.get(f"/tutor/{tutor_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


async def test_create_duplicate_tutor_conflict(client: AsyncClient, unique_tutor_data: dict) -> None:
    create_resp = await client.post(url="/tutor/", json=unique_tutor_data)
    assert create_resp.status_code == status.HTTP_201_CREATED

    dup_resp = await client.post(url="/tutor/", json=unique_tutor_data)
    assert dup_resp.status_code == status.HTTP_409_CONFLICT


async def test_get_nonexistent_tutor(client: AsyncClient) -> None:
    non_existent_id = f"nonexistent_{uuid.uuid4().hex[:8]}"
    resp = await client.get(f"/tutor/{non_existent_id}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_update_tutor_missing_id(client: AsyncClient) -> None:
    resp = await client.put(url="/tutor/", json={"name": "No ID Tutor"})
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


async def test_delete_tutor_missing_id(client: AsyncClient) -> None:
    resp = await client.request(method="DELETE", url="/tutor/", json={})
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
