import os
from decimal import Decimal

os.environ["APP_ENV"] = "test"
os.environ["APP_DEBUG"] = "false"
os.environ["SECRET_KEY"] = "tinnova-vehicle-api-super-secret-key-tests-2026"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.api.dependencies.services import get_exchange_rate_service
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from tests.helpers import (
    TEST_ADMIN_CREDENTIALS,
    TEST_USER_CREDENTIALS,
    FixedExchangeRateService,
    create_user,
    get_access_token,
)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seeded_users(session_factory):
    with session_factory() as session:
        create_user(
            session,
            username=TEST_ADMIN_CREDENTIALS["username"],
            email=TEST_ADMIN_CREDENTIALS["email"],
            password=TEST_ADMIN_CREDENTIALS["password"],
            role=TEST_ADMIN_CREDENTIALS["role"],
        )
        create_user(
            session,
            username=TEST_USER_CREDENTIALS["username"],
            email=TEST_USER_CREDENTIALS["email"],
            password=TEST_USER_CREDENTIALS["password"],
            role=TEST_USER_CREDENTIALS["role"],
        )

    return {
        "admin": TEST_ADMIN_CREDENTIALS,
        "user": TEST_USER_CREDENTIALS,
    }


@pytest.fixture
def exchange_rate_service():
    return FixedExchangeRateService(rate=Decimal("5.0000"))


@pytest.fixture
def client(session_factory, seeded_users, exchange_rate_service):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_exchange_rate_service] = lambda: exchange_rate_service

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token(client):
    return get_access_token(
        client,
        username=TEST_ADMIN_CREDENTIALS["username"],
        password=TEST_ADMIN_CREDENTIALS["password"],
    )


@pytest.fixture
def user_token(client):
    return get_access_token(
        client,
        username=TEST_USER_CREDENTIALS["username"],
        password=TEST_USER_CREDENTIALS["password"],
    )


@pytest.fixture
def admin_auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_auth_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
