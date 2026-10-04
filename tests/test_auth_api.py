"""Integration tests for authentication endpoints."""

import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    """Registering a new user should return 201 with user data."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User",
            "tenant_id": "test-tenant",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["tenant_id"] == "test-tenant"
    assert "hashed_password" not in data  # Never leak the hash
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Registering with an existing email should return 400."""
    payload = {
        "email": "duplicate@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "tenant_id": "test-tenant",
    }
    response1 = await client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201

    response2 = await client.post("/api/v1/auth/register", json=payload)
    assert response2.status_code == 400
    assert response2.json()["error"] == "email_already_exists"


@pytest.mark.asyncio
async def test_login_success(client):
    """Valid login should return a JWT token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "testpass123",
            "full_name": "Test User",
            "tenant_id": "test-tenant",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Wrong password should return 401."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw@example.com",
            "password": "testpass123",
            "full_name": "Test User",
            "tenant_id": "test-tenant",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_get_me_without_token(client):
    """Accessing /me without a token should return 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_token(client):
    """Accessing /me with a valid token should return the user."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "password": "testpass123",
            "full_name": "Me User",
            "tenant_id": "test-tenant",
        },
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
@pytest.mark.asyncio
async def test_get_me_with_tampered_token(client):
    """A modified or invalid JWT signature should return 401."""
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.invalidsignature"
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401
    assert "detail" in response.json()
@pytest.mark.asyncio
async def test_login_nonexistent_user_generic_error(client):
    """Non-existent email should return identical 401 as wrong password to prevent enumeration."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "somepassword123"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"



@pytest.mark.asyncio
async def test_register_invalid_email_format(client):
    """Invalid email formats should fail Pydantic validation with 422."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "testpass123",
            "full_name": "Test User",
            "tenant_id": "test-tenant",
        },
    )
    assert response.status_code == 422
