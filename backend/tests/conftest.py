import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

TEST_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def init_db():
    # Setup tables once for test suite
    Base.metadata.create_all(bind=engine)
    yield
    # Do not drop tables on PostgreSQL to avoid dropping development DB tables
    if "sqlite" in TEST_DATABASE_URL:
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
