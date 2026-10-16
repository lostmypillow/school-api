from pathlib import Path

import httpx
import pytest
import pytest_asyncio

from app.core.custom_http_client import CustomAsyncClient
from app.domains.courses.schemas import SemesterModel
from app.domains.tasks.scrape.sync_semesters import scrape_semesters
from app.domains.tasks.parquet_utils import read_parquet_records

PARQUET_SNAPSHOT_DIR = Path(__file__).resolve().parents[3] / "data" / "parquet"


@pytest_asyncio.fixture
async def live_client():
    """Provides a live CustomAsyncClient targeting NTUT course catalog with SSL verification disabled."""
    client = CustomAsyncClient(
        verify=False,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=10),
        timeout=30.0,
    )
    try:
        yield client
    finally:
        if not client.is_closed:
            await client.aclose()


@pytest.mark.asyncio
async def test_scrape_semesters_real_url(live_client: CustomAsyncClient):
    """Step 1: Test scraping semesters from NTUT catalog using a real URL.

    Fetches the catalog semester root page (Subj.jsp?format=-1), parses all
    semesters, validates them against SemesterModel, and compares with semesters.parquet snapshot.
    """
    ctx = {"client": live_client}

    # Retrieve real semester URL reference or fallback to root page
    parquet_path = PARQUET_SNAPSHOT_DIR / "semesters.parquet"
    sem_url = "Subj.jsp?format=-1"

    scraped_semesters: list[SemesterModel] = await scrape_semesters(ctx=ctx, url=sem_url)
    assert len(scraped_semesters) > 0, "Expected semester anchor tags from NTUT root page"

    # Validate each scraped semester using Pydantic SemesterModel
    validated_models: list[SemesterModel] = []
    for sem in scraped_semesters:
        model = SemesterModel.model_validate(sem)
        validated_models.append(model)

    print("\n" + "=" * 70)
    print(f"[STEP 1: Semesters] Scraped and validated {len(validated_models)} semesters from NTUT:")
    for m in validated_models[:5]:
        print(f"  - {m.name} -> link: {m.link} (year={m.year}, sem={m.sem})")
    print(f"  ... and {len(validated_models) - 5} more semesters.")
    print("=" * 70)

    assert len(validated_models) > 0
    assert all(m.year and m.sem and m.link for m in validated_models)

    if parquet_path.exists():
        snapshot_records = read_parquet_records(parquet_path)
        snapshot_ids = {r["id"] for r in snapshot_records if "id" in r}
        scraped_ids = {m.id for m in validated_models}
        common_ids = snapshot_ids.intersection(scraped_ids)
        print(f"[STEP 1: Validation] {len(common_ids)} scraped semesters match snapshot IDs in semesters.parquet.")
        assert len(common_ids) > 0
