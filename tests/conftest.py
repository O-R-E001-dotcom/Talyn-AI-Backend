"""Pytest fixtures for Talyn backend tests."""
import os

# Disabled suite-wide: ~150 auth hits from one IP would trip the limiter.
# Rate limiting itself is covered with it enabled in test_gaps.py.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

# Never inherit real credentials from a developer's .env. Without this, a
# local PAYSTACK_SECRET_KEY makes the suite take the live checkout path
# instead of the stub, and tests quietly depend on whether a developer has
# finished configuring their machine. Tests that need Paystack enable it
# themselves (see tests/test_paystack.py).
os.environ["PAYSTACK_SECRET_KEY"] = ""
os.environ["PAYSTACK_WEBHOOK_SECRET"] = ""
os.environ["PAYSTACK_API_URL"] = ""

# Same reasoning for SMTP. A developer's real mail credentials would make the
# suite attempt genuine sends against the live server, and a credential
# failure would surface as an unexpected 502 rather than as "unconfigured".
os.environ["SMTP_HOST"] = ""
os.environ["SMTP_USERNAME"] = ""
os.environ["SMTP_PASSWORD"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Isolated test database. The backend expects `talyn_test` to exist on the
# same Postgres server (see README).
TEST_DATABASE_URL = os.getenv(
    "TALYN_TEST_DATABASE_URL",
    "postgresql+psycopg://talyn:talyn_dev_password@localhost:5432/talyn_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def prepare_schema():
    """Create all tables once per test session."""
    from app.database import Base
    from app import models  # noqa: F401  ensure models are imported

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables(prepare_schema):
    """Truncate all tables before each test so tests start from a clean DB."""
    from app.database import Base

    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


@pytest.fixture()
def db_session(prepare_schema):
    session: Session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session):
    """TestClient with the DB session dependency overridden to the test DB."""
    from app.database import get_db
    from app.main import app

    def override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def admin_headers(client, db_session):
    """Headers for an admin user (course management)."""
    from sqlalchemy import select

    from app.models import User

    client.post(
        "/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "secret12345",
            "learner_name": "Admin",
        },
    )
    user = db_session.scalar(select(User).where(User.email == "admin@example.com"))
    user.is_admin = True
    db_session.commit()
    r = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "secret12345"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

# -- Fixtures -----------------------------------------------------------------


@pytest.fixture()
def creator_headers(client):
    client.post("/v1/auth/register", json={
        "email": "upload-creator@example.com", "password": "password123",
        "learner_name": "Uploader", "is_creator": True,
    })
    r = client.post("/v1/auth/login", json={
        "email": "upload-creator@example.com", "password": "password123",
    })
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def learner_headers(client):
    client.post("/v1/auth/register", json={
        "email": "upload-learner@example.com", "password": "password123",
        "learner_name": "Learner",
    })
    r = client.post("/v1/auth/login", json={
        "email": "upload-learner@example.com", "password": "password123",
    })
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def lesson_id(client, creator_headers, db_session):
    """A published lesson the creator owns."""
    from app.models import Course

    cid = client.post("/v1/courses", json={
        "title": "Upload Course", "description": "Has lessons",
        "category": "Design", "outcomes": ["Learn"],
        "target_audience": "All", "thumbnail_key": "t.png",
    }, headers=creator_headers).json()["id"]
    mid = client.post(f"/v1/courses/{cid}/modules", json={"title": "M"},
                      headers=creator_headers).json()["id"]
    lid = client.post(f"/v1/courses/{cid}/lessons", json={
        "module_id": mid, "title": "Lesson One", "topic": "Basics",
        "content": "Content.",
    }, headers=creator_headers).json()["id"]
    db_session.get(Course, cid).status = "published"
    db_session.commit()
    return lid