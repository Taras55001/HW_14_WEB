from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from src.database.models import User
from tests.conftest import TestingSessionLocal

user_mock = {
    "name": "borisjhonson",
    "email": "greatbritan@england.com",
    "password": "putinmustdie",
}


def test_create_user(client, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    response = client.post("/auth/signup", json=user_mock)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data.get("email") == user_mock.get("email")
    assert data.get("name") == user_mock.get("name")


def test_repeat_create_user(client, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    response = client.post("/auth/signup", json=user_mock)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data.get("detail") == "Account already exist"


def test_login_user_not_confirmed(client, monkeypatch):
    response = client.post(
        "/auth/login",
        data={
            "username": user_mock.get("email"),
            "password": user_mock.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data.get("detail") == "Email not confirmed"


@pytest.mark.asyncio
async def test_login_user(client, monkeypatch):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_mock.get('email')))
        current_user = current_user.scalar_one_or_none()
        current_user.confirmed = True
        await session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": user_mock.get("email"),
            "password": user_mock.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_user(client, monkeypatch):

    response = client.post(
        "/auth/login",
        data={
            "username": user_mock.get("email"),
            "password": "password",
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data.get("detail") == "Incorrect password"


def test_login_wrong_email_user(client, monkeypatch):

    response = client.post(
        "/auth/login",
        data={
            "username": "email@email.com",
            "password": user_mock.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data.get("detail") == "Invalid email"


def test_login_validation_user(client, monkeypatch):

    response = client.post(
        "/auth/login",
        data={
            "password": user_mock.get("password"),
        },
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data
