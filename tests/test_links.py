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
@pytest.mark.asyncio
async def test_delete_link_invalidates_cache(client, db_session):
    """Ensure deleting a link removes it from the DB and clears the Redis cache."""
    
    # 1. Create a real user and get a valid token
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "delete-test@example.com",
            "password": "testpassword123",
            "full_name": "Delete Test User",
            "tenant_id": "test-tenant"
        }
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "delete-test@example.com", "password": "testpassword123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create the link
    create_response = await client.post(
        "/api/v1/links/",
        json={"original_url": "https://www.google.com", "custom_code": "del-test"},
        headers=headers
    )
    assert create_response.status_code == 201
    link_id = create_response.json()["id"]
    short_code = create_response.json()["short_code"]

    # 3. Trigger a redirect to populate the Redis cache
    redirect_response = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 302
    
    # Verify it is in the cache
    from app.db.redis import redis_client
    cached_value = await redis_client.get(f"link:{short_code}")
    assert cached_value == "https://www.google.com"

    # 4. Delete the link
    delete_response = await client.delete(f"/api/v1/links/{link_id}", headers=headers)
    assert delete_response.status_code == 204

    # 5. Verify the database row is gone
    from sqlalchemy import select
    from app.models.link import Link
    db_result = await db_session.execute(select(Link).where(Link.id == link_id))
    assert db_result.scalars().first() is None

    # 6. Verify the Redis cache is gone
    cached_value_after_delete = await redis_client.get(f"link:{short_code}")
    assert cached_value_after_delete is None

    # 7. Verify the redirect now fails with a 404
    failed_redirect = await client.get(f"/{short_code}", follow_redirects=False)
    assert failed_redirect.status_code == 404