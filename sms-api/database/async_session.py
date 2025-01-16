from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager

# Database connection URL
connection_url = "mssql+aioodbc://testsql:test123456@192.168.2.8/?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

# Creating the SQLAlchemy async engine and sessionmaker
async_engine = create_async_engine(connection_url, pool_size=100, max_overflow=0, pool_pre_ping=True)
create_session = async_sessionmaker(async_engine, expire_on_commit=False)

# Define an async context manager to manage the lifecycle of the session
@asynccontextmanager
async def async_session():
    async with create_session() as session:
        yield session
