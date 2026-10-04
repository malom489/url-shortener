import pytest
from httpx import AsyncClient


@pytest.fixture
async def user_a_auth_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@example.com",
            "password": "Password123!",
            "full_name": "User A",
            "tenant_id": "tenant-a",
        },
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "usera@example.com", "password": "Password123!"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user_b_auth_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "userb@example.com",
            "password": "Password123!",
            "full_name": "User B",
            "tenant_id": "tenant-b",
        },
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "userb@example.com", "password": "Password123!"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_short_link(client: AsyncClient, user_a_auth_headers: dict):
    """Authenticated user should be able to create a short link."""
    response = await client.post(
        "/api/v1/links/",  # Added trailing slash
        json={"original_url": "https://example.com/long-target-path"},
        headers=user_a_auth_headers,
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com/long-target-path"


@pytest.mark.asyncio
async def test_public_redirect(client: AsyncClient, user_a_auth_headers: dict):
    """Redirection should work publicly without requiring authorization headers."""
    # 1. Create link
    create_res = await client.post(
        "/api/v1/links/",  # Added trailing slash
        json={"original_url": "https://example.com/redirect-target"},
        headers=user_a_auth_headers,
    )
    assert create_res.status_code in (200, 201)
    short_code = create_res.json()["short_code"]

    # 2. Access redirect unauthenticated
    redirect_res = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_res.status_code in (301, 302, 307)
    assert redirect_res.headers["location"] == "https://example.com/redirect-target"


@pytest.mark.asyncio
async def test_bola_prevent_cross_user_link_deletion(
    client: AsyncClient, user_a_auth_headers: dict, user_b_auth_headers: dict
):
    """User B must NOT be able to delete a link owned by User A (BOLA Check)."""
    # 1. User A creates link
    create_res = await client.post(
        "/api/v1/links/",  # Added trailing slash
        json={"original_url": "https://example.com/user-a-private-link"},
        headers=user_a_auth_headers,
    )
    assert create_res.status_code in (200, 201)
    link_id = create_res.json()["id"]

    # 2. User B attempts to delete User A's link
    delete_res = await client.delete(
        f"/api/v1/links/{link_id}",
        headers=user_b_auth_headers,
    )

    # Must fail with 403 Forbidden or 404 Not Found
    assert delete_res.status_code in (403, 404)