URL-SHORTENER

A production grade  url shortener built  with FastAPI,postgreSQL,and redis,designed from firs principle

I built this to learn how real backend systems are structured: how authentication works under the hood, how multi-tenant data isolation is enforced, how the redirect hot path can be made fast with caching, and how schema changes are managed safely in production.

## FEATURES
- **User authentication** — Registration and login with bcrypt password hashing and JWT access tokens
- **Multi-tenant isolation** — Every user belongs to a tenant; data is scoped at the query level
- **URL shortening** — Cryptographically secure short code generation using `secrets`, not `random`
- **Fast redirects** — Redis cache-aside pattern on the redirect hot path
- **Click tracking** — Atomic counter increments with no race conditions
- **Custom short codes** — Optional user-provided codes with collision handling

- **Database migrations** — Version-controlled schema changes via Alembic
- **Tested** — Unit and integration tests with pytest (76% coverage)
- **Containerized** — Docker Compose for API, PostgreSQL, and Redis

## Tech Stack


| Layer | Technology |
|:---|:---|
| Framework | FastAPI |
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (PyJWT) + bcrypt |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio + httpx |
| Container | Docker + Docker Compose |

## Architectur
     Client 
       │ HTTP
       ▼
    FastAPI (API Layer) 

│ /api/v1/auth (register/login)│

 /api/v1/links (CRUD, auth) │ 
 /{short_code} (public redirect)
 └──────────────────────────────   │           
    ▼           
┌──────────┐        ┌──────────┐
│ Redis │ │          PostgreSQL│
│ (cache) │          │(persist) │
└──────────┘        └──
 

 
CACHE_TTL = 3600  # 1 hour


@router.get("/{short_code}")
async def redirect_to_url(short_code: str):
    """Redirect a short code to its original URL. Public endpoint."""

    # 1. Try Redis first (fast path)
    cache_key = f"link:{short_code}"
    cached_url = await redis_client.get(cache_key)

    if cached_url:
        await _increment_click(short_code)
        return RedirectResponse(
            url=cached_url,
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
        )

    # 2. Cache miss — query PostgreSQL
    async with async_session() as db:
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        link = result.scalar_one_or_none()

        if not link:
            raise LinkNotFoundError(
                message=f"Short code '{short_code}' not found.",
                details={"short_code": short_code},
            )
 Design Decisions
The engineering choices that shaped this project, and why.

Why secrets instead of random for short codes
Python's random module uses the Mersenne Twister algorithm—it's deterministic and predictable. Given enough outputs, an attacker can infer the internal state and predict future codes. The secrets module reads from the OS's cryptographically secure RNG (/dev/urandom), making short codes unpredictable. For anything security-adjacent, secrets is the correct choice.

Why a denormalized click_count on the links table
Every redirect could run SELECT COUNT(*) FROM clicks WHERE link_id = X, but that's a full table scan under load. Instead, we store a counter column on the link row and increment it atomically with UPDATE links SET click_count = click_count + 1. This trades a small amount of write amplification for read performance on the hot path. The counter is the source of truth for the click total; a separate clicks table (future work) will hold per-event details for analytics.

Why multi-tenancy via a tenant_id column (not separate schemas or databases)
Every row has a tenant_id, and every query filters by the authenticated user's tenant. This is simpler to reason about than running separate PostgreSQL schemas or databases per tenant, and it scales to thousands of tenants on a single database. The trade-off is that one noisy tenant can affect others—acceptable at this stage, and mitigatable later with connection pool partitioning or per-tenant rate limits.

Why JWT over server-side sessions
JWT is stateless. Any API instance can verify a token using the shared secret key without needing a central session store. This makes horizontal scaling trivial—spin up more instances, and they all work. The trade-off is that tokens can't be revoked before they expire. We mitigate this with short-lived access tokens (30 minutes).

Why Redis on the redirect path
The /{short_code} endpoint runs on every click. PostgreSQL lookups take roughly 5–20ms depending on load; Redis lookups take under 1ms. For a read-heavy workload where popular links are clicked repeatedly, this is a 10–100x speedup. We use a TTL (1 hour) instead of explicit invalidation to keep things simple—links change rarely, so a short window of staleness is acceptable

Why Alembic over create_all()
Base.metadata.create_all() only creates tables that don't exist—it doesn't alter existing ones. During development I hit bugs caused by a column defined as Integer in the database but String in the model. Alembic migrations make every schema change versioned, reviewable, reversible, and repeatable. This is the difference between a hobby project and something you can deploy to production.

Testing
The test suite covers pure functions (short code generation, password hashing) and the full API surface (registration, login, authentication, protected endpoints).

bash
# Run all tests
pytest -v

# With coverage report
pytest --cov=app --cov-report=term-missing
Tests use a separate urlshortener_test database. Each test runs in isolation—tables are created and dropped around every test function via fixtures in tests/conftest.py. FastAPI's dependency_overrides replaces the production database session with the test session, so tests never touch real data.

Project Structure
text
urlshortener/
├── app/
│   ├── api/v1/          # HTTP endpoints
│   │   ├── api.py       # Router aggregation
│   │   ├── auth.py      # /auth endpoints
│   │   ├── links.py     # /links endpoints
│   │   └── redirect.py  # /{short_code} redirect
│   ├── core/            # Cross-cutting concerns
│   │   ├── config.py    # Settings (Pydantic)
│   │   ├── exceptions.py# Domain exceptions
│   │   └── handlers.py  # Exception → HTTP mapping
│   ├── db/              # Database and cache connections
│   │   ├── session.py   # Async SQLAlchemy session
│   │   └── redis.py     # Async Redis client
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # Business logic
│   │   ├── auth.py      # Hashing, JWT, get_current_user
│   │   └── short_code.py# Short code generation
│   └── main.py          # FastAPI app entry point
├── alembic/             # Database migrations
├── tests/               # Test suite
├── compose.yaml         # Docker Compose
├── requirements.txt     # Python dependencies
└── README.md
What's Next
Planned improvements, roughly in priority order:

□ Structured logging — JSON-formatted logs with request IDs for tracing
□ Rate limiting — Per-user and per-endpoint limits to prevent abuse
□ Observability — Prometheus metrics and a Grafana dashboard
□ Link analytics — Clicks by country, referrer, and time window
□ CI/CD pipeline — GitHub Actions running tests on every push
□ Production deployment — Cloud VM with Nginx reverse proxy and TLS
□ Link expiration — Optional TTL per link
□ Link deletion — With cache invalidation

---

