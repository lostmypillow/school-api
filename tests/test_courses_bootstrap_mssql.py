import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from app.core.initialize import DB
from app.core.models import Base, Course, Department, DepartmentYear, Semester
from app.domains.courses.bootstrap_mssql import bootstrap_mssql


@pytest_asyncio.fixture
async def mssql_mock_engine():
    """Provides a fresh SQLite in-memory engine standing in for the target MSSQL engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def mssql_mock_db(mssql_mock_engine: AsyncEngine) -> DB:
    db = DB.__new__(DB)
    db.engine = mssql_mock_engine
    db.session_factory = async_sessionmaker(
        bind=mssql_mock_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    return db


@pytest.mark.asyncio
async def test_bootstrap_mssql_full_migration(
    test_db: DB, mssql_mock_db: DB, mssql_mock_engine: AsyncEngine
):
    """Test bootstrap_mssql copies all tables and records in dependency order."""
    # 1. Populate source SQLite
    async with test_db.get_session() as session:
        sem = Semester(
            id="112_1", year="112", sem="1", link="Subj.jsp?year=112&sem=1"
        )
        dep = Department(
            id="112_1_300",
            semester_id="112_1",
            year="112",
            sem="1",
            code="300",
            name="Computer Science",
            link="Subj.jsp?year=112&sem=1&code=300",
        )
        dy = DepartmentYear(
            id="112_1_300_101",
            department_id="112_1_300",
            year="112",
            sem="1",
            code="101",
            name="CS Year 1",
            link="Subj.jsp?year=112&sem=1&code=101",
        )
        course = Course(
            id="112_1_101_300001",
            department_year_id="112_1_300_101",
            year="112",
            sem="1",
            code="300001",
            name="Data Structures",
            credits=3,
            classroom="Room 101",
            students_enrolled=40,
            students_dropped=0,
        )
        session.add_all([sem, dep, dy, course])
        await session.commit()

    ctx = {"database": test_db, "mssql_db": mssql_mock_db}

    # 2. Run migration
    await bootstrap_mssql(ctx)

    # 3. Verify target database has all data
    async with mssql_mock_engine.connect() as conn:
        sem_rows = (await conn.execute(select(Semester))).all()
        dep_rows = (await conn.execute(select(Department))).all()
        dy_rows = (await conn.execute(select(DepartmentYear))).all()
        course_rows = (await conn.execute(select(Course))).all()

        assert len(sem_rows) == 1
        assert sem_rows[0].id == "112_1"

        assert len(dep_rows) == 1
        assert dep_rows[0].name == "Computer Science"

        assert len(dy_rows) == 1
        assert dy_rows[0].code == "101"

        assert len(course_rows) == 1
        assert course_rows[0].name == "Data Structures"


@pytest.mark.asyncio
async def test_bootstrap_mssql_empty_source(
    test_db: DB, mssql_mock_db: DB, mssql_mock_engine: AsyncEngine
):
    """Test bootstrap_mssql creates tables on target even when source database is empty."""
    ctx = {"database": test_db, "mssql_db": mssql_mock_db}

    await bootstrap_mssql(ctx)

    async with mssql_mock_engine.connect() as conn:
        sem_count = await conn.scalar(select(func.count(Semester.id)))
        assert sem_count == 0


@pytest.mark.asyncio
async def test_bootstrap_mssql_deduplication(
    test_db: DB, mssql_mock_db: DB, mssql_mock_engine: AsyncEngine
):
    """Test bootstrap_mssql skips existing primary keys in destination database to avoid duplicate inserts."""
    sem1 = Semester(
        id="112_1", year="112", sem="1", link="Subj.jsp?year=112&sem=1"
    )
    sem2 = Semester(
        id="112_2", year="112", sem="2", link="Subj.jsp?year=112&sem=2"
    )

    # Source has sem1 and sem2
    async with test_db.get_session() as session:
        session.add_all([sem1, sem2])
        await session.commit()

    # Pre-create tables and insert sem1 in destination
    async with mssql_mock_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            Semester.__table__.insert(),
            [{"id": "112_1", "year": "112", "sem": "1", "link": "old_link"}],
        )

    ctx = {"database": test_db, "mssql_db": mssql_mock_db}

    # Run migration
    await bootstrap_mssql(ctx)

    # Destination should have both sem1 (original link) and sem2
    async with mssql_mock_engine.connect() as conn:
        rows = (await conn.execute(select(Semester))).all()
        assert len(rows) == 2
        sem1_row = next(r for r in rows if r.id == "112_1")
        sem2_row = next(r for r in rows if r.id == "112_2")
        assert sem1_row.link == "old_link"
        assert sem2_row.link == "Subj.jsp?year=112&sem=2"


@pytest.mark.asyncio
async def test_bootstrap_mssql_large_dataset_partitions(
    test_db: DB, mssql_mock_db: DB, mssql_mock_engine: AsyncEngine
):
    """Test bootstrap_mssql processes data across multiple partition chunks (e.g. > 5000 rows)."""
    # Insert 5010 semesters into source database with unique (year, sem)
    semesters = [
        {
            "id": f"sem_{i}",
            "year": f"Y{i}",
            "sem": "1",
            "link": f"link_{i}",
        }
        for i in range(5010)
    ]

    async with test_db.get_session() as session:
        await session.execute(Semester.__table__.insert(), semesters)
        await session.commit()

    ctx = {"database": test_db, "mssql_db": mssql_mock_db}

    await bootstrap_mssql(ctx)

    async with mssql_mock_engine.connect() as conn:
        count = await conn.scalar(select(func.count(Semester.id)))
        assert count == 5010
