# Plan: Add MCP (Model Context Protocol) to Endurain

## Overview

Add a remote HTTP-based MCP server to Endurain, integrated into the existing FastAPI backend at `/mcp`. Users authenticate via long-lived API keys generated from a new Settings > API Keys page. MCP tools provide full read/write access to activities, health data, gear, and profile — all scoped to the authenticated user.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Transport | HTTP streamable-http at `/mcp` | Integrated into existing FastAPI, no sidecar process |
| Server mode | `stateless_http=True, json_response=True` | Production-recommended, no server-side MCP session state |
| Scope | User-scoped only | Each API key is tied to a user; tools only access that user's data |
| Auth | Long-lived API keys (SHA-256 hashed in DB) | Simpler than JWT 15-min expiry; validated via MCP SDK's `TokenVerifier` |
| Write access | Full read/write across all domains | Per user decision |
| MCP SDK | `mcp>=1.9.0` | Stable streamable-http support |

## Scope Exclusions

- No stdio transport (HTTP only)
- No admin-scoped MCP access (user-scoped only)
- No OAuth2 flow for MCP clients (API key only)
- No Strava/Garmin sync trigger tools via MCP
- No `/.well-known/mcp` auto-discovery (future work)
- No browser-based MCP client support

## Validation Environment

Each step must be validated using the local dev environment before moving on. The dev stack is started via `docker compose up -d` from the project root, which runs:

- **endurain** — the backend (FastAPI + frontend), built from `docker/Dockerfile`, with `backend/app` bind-mounted for live code changes. Available at `http://localhost:8080`.
- **postgres** — PostgreSQL 17, available at `localhost:5432`.

Secrets and config are in `.env` (gitignored). Both files (`docker-compose.yml` and `.env`) already exist in the project root.

**Validation loop for each step:**
1. `docker compose build && docker compose up -d` (rebuild and start/restart services)
2. Check container logs: `docker compose logs endurain --tail 50` (no startup errors)
3. Run step-specific checks (e.g., verify table exists, test API endpoints via `curl`, confirm frontend builds)
4. For steps with UI changes: open browser at `http://localhost:8080`, log in, and visually verify the feature works (navigate, click, submit forms, check responses)
5. If any check fails, fix the issue and repeat from step 1. Iterate until all checks pass before proceeding to the next step

## Dependency Graph

```
Step 1 (DB model) ──► Step 2 (CRUD/Router) ──► Step 3 (Validation util)
                                                       │
Step 4 (Frontend UI) ◄── depends on Step 2             │
                                                       ▼
Step 5 (mcp dep) ──► Step 6 (MCP skeleton + mount) ◄───┘
                           │
              ┌────────────┼────────────┬──────────┐
              ▼            ▼            ▼          ▼
         Step 7       Step 8       Step 9     Step 10
        (Activities)  (Health)     (Gear)     (Profile)
              │            │            │          │
              └────────────┼────────────┘          │
                           ▼                       │
                      Step 11 (Resources) ◄────────┘
                           │
                           ▼
                      Step 12 (Prompts)
                           │
                           ▼
                      Step 13 (E2E test)
                           │
                           ▼
                      Step 14 (Docs)
```

Steps 7–10 can be implemented in parallel (independent tool domains).
Step 4 can be done in parallel with Steps 5–6 (frontend vs. backend).

---

## Phase 1 — API Key Infrastructure

### Step 1: Database Model + Alembic Migration ✅ DONE

**Goal:** Create the `user_api_keys` table.

**New files:**
- `backend/app/api_keys/__init__.py` — empty
- `backend/app/api_keys/models.py`

**Model definition (`UserApiKey`):**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `Integer` | Primary key, autoincrement |
| `user_id` | `Integer` | FK → `users.id`, NOT NULL, indexed |
| `name` | `String(100)` | NOT NULL (user-provided label) |
| `key_prefix` | `String(8)` | NOT NULL (first 8 chars of raw key, for display) |
| `key_hash` | `String(64)` | NOT NULL, unique, indexed (SHA-256 hex digest) |
| `created_at` | `DateTime` | NOT NULL, default `utcnow` |
| `last_used_at` | `DateTime` | Nullable |
| `expires_at` | `DateTime` | Nullable |

Relationship: `user = relationship("Users")` (references the `Users` model in `users/users/models.py`).

Follow the model pattern from `backend/app/auth/mfa_backup_codes/models.py` — import `Base` from `core.database`.

**Migration:** After creating the model, generate the Alembic migration:

```bash
cd backend/app && alembic revision --autogenerate -m "add_user_api_keys_table"
```

**Validation:**

```bash
# 1. Apply migration
cd backend/app && alembic upgrade head

# 2. Verify table exists (connect to PostgreSQL)
# \d user_api_keys → shows all columns, FK on user_id, unique index on key_hash

# 3. Server starts cleanly
cd backend/app && uvicorn main:app --reload
# → No errors in startup logs
```

---

### Step 2: API Keys Backend Module (CRUD + Schema + Router) ✅ DONE

**Goal:** Full CRUD API for managing API keys at `/api/v1/api_keys`.

**New files:**
- `backend/app/api_keys/schema.py`
- `backend/app/api_keys/crud.py`
- `backend/app/api_keys/router.py`

**Modify:**
- `backend/app/core/routes.py` — register the new router

#### schema.py

```python
from datetime import datetime
from pydantic import BaseModel, Field

class ApiKeyCreate(BaseModel):
    name: str = Field(..., max_length=100)

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None

    class Config:
        from_attributes = True

class ApiKeyCreated(ApiKeyResponse):
    full_key: str  # returned only once on creation
```

#### crud.py

Functions to implement:

- `create_api_key(user_id: int, name: str, db: Session) -> tuple[UserApiKey, str]`
  - Generate raw key: `secrets.token_urlsafe(32)` (produces ~43 chars)
  - Compute prefix: first 8 chars of raw key
  - Compute hash: `hashlib.sha256(raw_key.encode()).hexdigest()`
  - Insert `UserApiKey` row with `user_id`, `name`, `key_prefix`, `key_hash`
  - Return `(model_instance, raw_key)`
- `list_user_api_keys(user_id: int, db: Session) -> list[UserApiKey]`
  - Query filtered by `user_id`, ordered by `created_at desc`
- `delete_api_key(user_id: int, key_id: int, db: Session) -> bool`
  - Delete where `id == key_id AND user_id == user_id` (ownership check)
  - Raise HTTP 404 if not found, return `True` if deleted

Follow the error handling pattern from `backend/app/gears/gear/crud.py` — try/except with `core_logger.print_to_log()` and `HTTPException`.

#### router.py

```python
router = APIRouter()

# POST / → create_api_key(), returns ApiKeyCreated
# GET / → list_user_api_keys(), returns list[ApiKeyResponse]
# DELETE /{key_id} → delete_api_key(), returns 204 No Content
```

All endpoints:
- `db: Session = Depends(get_db)` from `core.database`
- Auth is inherited from route registration (`Depends(auth_security.validate_access_token)`)
- Extract `user_id` via `auth_security.get_sub_from_access_token()`

#### Register in core/routes.py

Add import (alphabetically, before `auth_router`):

```python
import api_keys.router as api_keys_router
```

Add registration (alphabetically, before `activities_router`):

```python
router.include_router(
    api_keys_router.router,
    prefix=core_config.ROOT_PATH + "/api_keys",
    tags=["api_keys"],
    dependencies=[Depends(auth_security.validate_access_token)],
)
```

**Validation:**

```bash
# 1. Server starts
cd backend/app && uvicorn main:app --reload

# 2. Get a JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=<user>&password=<pass>"
# → note the access_token

# 3. Create an API key
curl -X POST http://localhost:8000/api/v1/api_keys \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -H "X-Client-Type: web" \
  -H "X-CSRF-Token: <csrf>" \
  -d '{"name": "test key"}'
# → returns ApiKeyCreated with full_key

# 4. List keys
curl http://localhost:8000/api/v1/api_keys \
  -H "Authorization: Bearer <jwt>" \
  -H "X-Client-Type: web"
# → returns list with 1 key (prefix visible, no full_key)

# 5. Delete key
curl -X DELETE http://localhost:8000/api/v1/api_keys/<id> \
  -H "Authorization: Bearer <jwt>" \
  -H "X-Client-Type: web" \
  -H "X-CSRF-Token: <csrf>"
# → 204 No Content

# 6. List again → empty

# 7. Verify another user cannot delete the first user's key → 404

# 8. Frontend still builds
cd frontend/app && npm run build
```

---

### Step 3: API Key Validation Utility ✅ DONE

**Goal:** A utility function to validate raw API keys against the database. Used by the MCP `TokenVerifier` in Phase 2.

**New file:** `backend/app/api_keys/utils.py`

**Function signature:**

```python
def validate_api_key(token: str, db: Session) -> Users | None:
```

**Logic:**
1. Compute: `key_hash = hashlib.sha256(token.encode()).hexdigest()`
2. Query: `UserApiKey` where `key_hash == computed_hash`
3. If not found → return `None`
4. If found and `expires_at` is set and in the past → return `None`
5. Update `last_used_at = datetime.utcnow()`, `db.commit()`
6. Return the associated `User` object (via the `user` relationship)

**Important:** This is NOT a FastAPI dependency — it's a plain function called by the MCP `TokenVerifier` (Step 6) which manages its own DB session.

**Validation:**

```bash
# 1. Server starts
cd backend/app && uvicorn main:app --reload

# 2. Quick manual test (or write backend/tests/api_keys/test_utils.py):
#    - Create a key via crud.create_api_key()
#    - Call validate_api_key() with the raw key → returns User
#    - Call validate_api_key() with random string → returns None
#    - Create a key with expires_at in the past → validate returns None

# 3. Frontend still builds
cd frontend/app && npm run build
```

---

### Step 4: Frontend — API Key Management UI ✅ DONE

**Goal:** Add an "API Keys" section to the Settings page where users can create, view, and delete API keys.

**New files:**
- `frontend/app/src/services/apiKeysService.js`
- `frontend/app/src/components/Settings/SettingsApiKeysZone.vue`

**Modify:**
- `frontend/app/src/components/Settings/SettingsSideBarComponent.vue`
- `frontend/app/src/views/SettingsView.vue`

#### 4a. Service (`apiKeysService.js`)

Follow the pattern from `profileService.js`:

```javascript
import {
  fetchGetRequest,
  fetchPostRequest,
  fetchDeleteRequest,
} from '@/utils/serviceUtils'

export const apiKeys = {
  listApiKeys() {
    return fetchGetRequest('api_keys')
  },
  createApiKey(data) {
    return fetchPostRequest('api_keys', data)
  },
  deleteApiKey(keyId) {
    return fetchDeleteRequest(`api_keys/${keyId}`)
  },
}
```

#### 4b. Sidebar entry (`SettingsSideBarComponent.vue`)

Add a new `<li>` item after the existing "import" entry (before the closing `</ul>`):

```html
<li class="nav-item">
  <a
    href="#"
    class="nav-link link-body-emphasis"
    :class="{ active: activeSection === 'apiKeys' }"
    @click.prevent="changeActive('apiKeys')"
  >
    <font-awesome-icon :icon="['fas', 'fa-key']" />
    <span class="ms-1">{{ $t('settingsSideBar.apiKeysSection') }}</span>
  </a>
</li>
```

Add i18n key `settingsSideBar.apiKeysSection` = `"API Keys"` in the relevant locale files.

#### 4c. Zone component (`SettingsApiKeysZone.vue`)

Bootstrap card layout with:

- **Table** listing existing keys: columns for Name, Key Prefix (`xxxx****`), Created, Last Used, Delete button
- **Create form:** text input for name + submit button
- **On creation:** display the full key in an alert/modal with a copy-to-clipboard button and a warning "This key will not be shown again"
- **Info box** below the table showing the MCP connection details:
  ```
  URL: https://<your-host>/mcp
  Header: Authorization: Bearer <your-api-key>
  ```

Follow the component pattern from `SettingsSecurityZone.vue` (Bootstrap forms, v-model binding, `push.success()` / `push.error()` for notifications).

#### 4d. SettingsView.vue changes

Add import:

```javascript
import SettingsApiKeysZone from '../components/Settings/SettingsApiKeysZone.vue'
```

Add conditional rendering (after the `SettingsImportZone` block):

```html
<SettingsApiKeysZone v-if="activeSection === 'apiKeys'" />
```

In the `onMounted` logic, `'apiKeys'` is handled as a non-admin tab (falls through to `else` → `activeSection.value = route.query.tab`).

**Validation:**

```bash
# 1. No new npm deps needed
cd frontend/app && npm install

# 2. Build succeeds
npm run build

# 3. Format passes
npm run format

# 4. Dev server runs
npm run dev
# → open http://localhost:5173/settings?tab=apiKeys

# 5. Manual checks:
#    - Sidebar shows "API Keys" item
#    - Clicking it shows the zone component
#    - Create a key → full key displayed once
#    - Key appears in list with prefix
#    - Delete a key → removed from list
#    - Refresh page → key persists in list (fetched from API)

# 6. Backend still starts
cd backend/app && uvicorn main:app --reload
```

---

## Phase 2 — MCP Server

### Step 5: Add MCP Dependency ✅ DONE

**Goal:** Add the `mcp` Python package to the project.

**Modify:** `backend/pyproject.toml`

Add under `[tool.poetry.dependencies]`:

```toml
mcp = ">=1.9.0"
```

No `[cli]` extra needed — we only use the SDK, not the mcp CLI tools.

**Validation:**

```bash
# 1. Lock resolves
cd backend && poetry lock

# 2. Install succeeds
poetry install

# 3. SDK is importable
cd app && python -c "from mcp.server.fastmcp import FastMCP; print('OK')"
# → prints OK

# 4. Server starts
uvicorn main:app --reload

# 5. Frontend still builds
cd ../../frontend/app && npm run build
```

---

### Step 6: MCP Module Skeleton + Auth + FastAPI Mount

**Goal:** Create the MCP server instance with authentication, mount it into FastAPI, and verify it responds to MCP protocol requests.

**New files:**
- `backend/app/mcp_module/__init__.py` — empty
- `backend/app/mcp_module/server.py`
- `backend/app/mcp_module/auth.py`
- `backend/app/mcp_module/utils.py`

> **Note on naming:** The local module is named `mcp_module` (not `mcp`) to avoid a naming collision with the `mcp` pip package. All internal imports use `import mcp_module.server` etc.

**Modify:**
- `backend/app/core/config.py` — add `MCP_ENABLED`
- `backend/app/core/middleware.py` — add `/mcp` to CSRF exempt prefixes
- `backend/app/main.py` — mount MCP app, session manager lifecycle

#### 6a. Auth (`mcp_module/auth.py`)

Implement the MCP SDK's `TokenVerifier` protocol:

```python
from mcp.server.auth.provider import AccessToken, TokenVerifier
from core.database import SessionLocal
import api_keys.utils as api_keys_utils


class EndurainTokenVerifier(TokenVerifier):
    """Validates Endurain API keys for MCP authentication."""

    async def verify_token(self, token: str) -> AccessToken | None:
        db = SessionLocal()
        try:
            user = api_keys_utils.validate_api_key(token, db)
            if user is None:
                return None
            return AccessToken(
                token=token,
                client_id=str(user.id),
                scopes=["read", "write"],
            )
        finally:
            db.close()
```

#### 6b. Utils (`mcp_module/utils.py`)

```python
from mcp.server.fastmcp import Context
from core.database import SessionLocal


def get_user_id(ctx: Context) -> int:
    """Extract user_id from the MCP auth context."""
    return int(ctx.request_context.access_token.client_id)


def get_db():
    """Get a new database session. Caller must close it."""
    return SessionLocal()
```

#### 6c. Server (`mcp_module/server.py`)

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl
from mcp_module.auth import EndurainTokenVerifier
import core.config as core_config

mcp_server = FastMCP(
    "Endurain",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    token_verifier=EndurainTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(core_config.ENDURAIN_HOST),
        resource_server_url=AnyHttpUrl(core_config.ENDURAIN_HOST),
    ),
)

# Tool/resource/prompt imports will be added in Steps 7–12
```

`streamable_http_path="/"` is critical — without it, the MCP endpoint becomes `/mcp/mcp` instead of `/mcp`.

#### 6d. Config change (`core/config.py`)

Add after the `GEOCODES_MAPS_API` line:

```python
# MCP (Model Context Protocol) server
MCP_ENABLED = os.getenv("MCP_ENABLED", "true").lower() == "true"
```

#### 6e. CSRF exemption (`core/middleware.py`)

In `CSRFMiddleware.__init__`, add `/mcp` to `exempt_path_prefixes`:

```python
self.exempt_path_prefixes = [
    "/api/v1/public/idp/session/",
    "/mcp",  # MCP clients cannot send X-CSRF-Token headers
]
```

#### 6f. Mount in FastAPI (`main.py`)

In `create_app()`, after the static file mounts (before `return fastapi_app`):

```python
# Mount MCP server if enabled
if core_config.MCP_ENABLED:
    from mcp_module.server import mcp_server as endurain_mcp_server
    fastapi_app.mount("/mcp", endurain_mcp_server.streamable_http_app())
```

In `startup_event()`, add at the end:

```python
# Start MCP session manager
if core_config.MCP_ENABLED:
    from mcp_module.server import mcp_server as endurain_mcp_server
    app.state.mcp_session_cm = endurain_mcp_server.session_manager.run()
    await app.state.mcp_session_cm.__aenter__()
    core_logger.print_to_log_and_console("MCP server started")
```

In `shutdown_event()`, add (and make it `async def`):

```python
# Stop MCP session manager
if core_config.MCP_ENABLED and hasattr(app.state, "mcp_session_cm"):
    await app.state.mcp_session_cm.__aexit__(None, None, None)
    core_logger.print_to_log_and_console("MCP server stopped")
```

**Validation:**

```bash
# 1. Server starts without errors
cd backend/app && uvicorn main:app --reload
# → Logs show "MCP server started"

# 2. Test MCP endpoint WITHOUT auth → should be rejected
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
# → 401 Unauthorized

# 3. Create an API key (via JWT-authenticated endpoint)
API_KEY=$(curl -s -X POST http://localhost:8000/api/v1/api_keys \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -H "X-Client-Type: web" \
  -H "X-CSRF-Token: <csrf>" \
  -d '{"name":"mcp-test"}' | jq -r '.full_key')

# 4. Test MCP endpoint WITH valid API key → should return MCP initialize response
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
# → Response contains serverInfo.name = "Endurain"

# 5. Test with invalid key → 401
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid-key-12345" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
# → 401

# 6. Test MCP_ENABLED=false → /mcp returns 404
MCP_ENABLED=false uvicorn main:app --reload
curl -s http://localhost:8000/mcp
# → 404 Not Found

# 7. Frontend still builds
cd ../../frontend/app && npm run build
```

---

### Step 7: MCP Tools — Activities

**Goal:** Implement activity-related MCP tools.

**New files:**
- `backend/app/mcp_module/tools/__init__.py` — empty
- `backend/app/mcp_module/tools/activities.py`

**Modify:**
- `backend/app/mcp_module/server.py` — add import to register tools

**Tools to implement:**

Each tool uses the `@mcp_server.tool()` decorator, extracts `user_id` via `mcp_module.utils.get_user_id(ctx)`, opens a DB session via `mcp_module.utils.get_db()`, and calls existing crud functions.

| Tool | Description | CRUD function reference |
|------|-------------|------------------------|
| `list_activities(ctx, start_date?, end_date?, activity_type?, page_number=1, num_records=10)` | List user's activities with optional filters | `activities.activity.crud.get_user_activities()` |
| `get_activity(ctx, activity_id)` | Get a single activity by ID | `activities.activity.crud.get_user_activity_by_id()` |
| `get_activity_laps(ctx, activity_id)` | Get lap data for an activity | `activities.activity_laps.crud` |
| `get_activity_streams(ctx, activity_id)` | Get GPS/HR/power stream data | `activities.activity_streams.crud` |
| `delete_activity(ctx, activity_id)` | Delete an activity | `activities.activity.crud.delete_user_activity_by_id()` |

**Ownership enforcement:** All crud functions take `user_id` as a parameter and filter by it — data isolation is automatic.

**Pattern for each tool:**

```python
from mcp_module.server import mcp_server
from mcp_module.utils import get_user_id, get_db
from mcp.server.fastmcp import Context
import activities.activity.crud as activities_crud

@mcp_server.tool()
def list_activities(
    ctx: Context,
    start_date: str | None = None,
    end_date: str | None = None,
    activity_type: int | None = None,
    page_number: int = 1,
    num_records: int = 10,
) -> list[dict]:
    """List the user's fitness activities with optional date and type filters."""
    user_id = get_user_id(ctx)
    db = get_db()
    try:
        activities = activities_crud.get_user_activities(
            user_id, db, activity_type, start_date, end_date
        )
        return activities or []
    finally:
        db.close()
```

**Import in `mcp_module/server.py`** (add at the bottom):

```python
import mcp_module.tools.activities  # noqa: F401 — registers tools
```

**Validation:**

```bash
# 1. Server starts
cd backend/app && uvicorn main:app --reload

# 2. List available tools
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
# → Response includes list_activities, get_activity, etc.

# 3. Call list_activities
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_activities","arguments":{"page_number":1,"num_records":5}}}'
# → Returns user's activities (or empty list)

# 4. User isolation: User A's key does NOT return User B's activities

# 5. Frontend still builds
cd ../../frontend/app && npm run build
```

---

### Step 8: MCP Tools — Health

**Goal:** Health data tools (sleep, weight, steps).

**New file:** `backend/app/mcp_module/tools/health.py`

**Modify:** `backend/app/mcp_module/server.py` — add import

**Tools:**

| Tool | Description | Direction |
|------|-------------|-----------|
| `get_weight_data(ctx, start_date?, end_date?)` | Get weight records | Read |
| `get_steps_data(ctx, start_date?, end_date?)` | Get step count records | Read |
| `get_sleep_data(ctx, start_date?, end_date?)` | Get sleep records | Read |
| `log_weight(ctx, date, weight)` | Log a weight entry | Write |
| `log_steps(ctx, date, step_count)` | Log a step count entry | Write |

Delegates to existing crud in `health/health_weight/crud.py`, `health/health_steps/crud.py`, `health/health_sleep/crud.py`.

Add import in `mcp_module/server.py`:

```python
import mcp_module.tools.health  # noqa: F401
```

**Validation:**

```bash
# 1. Server starts
cd backend/app && uvicorn main:app --reload

# 2. tools/list shows health tools

# 3. Call get_weight_data → returns data (or empty)

# 4. Call log_weight with test data → succeeds
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"log_weight","arguments":{"date":"2026-04-25","weight":75.5}}}'

# 5. Call get_weight_data again → includes the new entry

# 6. User isolation: data only visible to the key's user

# 7. Frontend still builds
cd ../../frontend/app && npm run build
```

---

### Step 9: MCP Tools — Gear

**Goal:** Gear management tools.

**New file:** `backend/app/mcp_module/tools/gear.py`

**Modify:** `backend/app/mcp_module/server.py` — add import

**Tools:**

| Tool | Description | Direction |
|------|-------------|-----------|
| `list_gear(ctx, gear_type?)` | List user's gear | Read |
| `get_gear(ctx, gear_id)` | Get a specific gear item | Read |
| `create_gear(ctx, nickname, gear_type, brand_name?, model?)` | Create gear | Write |
| `delete_gear(ctx, gear_id)` | Delete gear | Write |

Delegates to `gears/gear/crud.py`. Ownership enforced via `user_id` filter.

Add import in `mcp_module/server.py`:

```python
import mcp_module.tools.gear  # noqa: F401
```

**Validation:**

```bash
# 1. Server starts
cd backend/app && uvicorn main:app --reload

# 2. tools/list shows gear tools

# 3. Call list_gear → returns user's gear

# 4. Call create_gear with test data → returns new gear

# 5. Call delete_gear → gear removed

# 6. User A cannot access User B's gear

# 7. Frontend still builds
cd ../../frontend/app && npm run build
```

---

### Step 10: MCP Tools — Profile

**Goal:** Read-only profile tools.

**New file:** `backend/app/mcp_module/tools/profile.py`

**Modify:** `backend/app/mcp_module/server.py` — add import

**Tools:**

| Tool | Description | Direction |
|------|-------------|-----------|
| `get_profile(ctx)` | Get user's profile info (name, username, city, units, etc.) | Read |
| `get_goals(ctx)` | Get user's training goals | Read |

Add import in `mcp_module/server.py`:

```python
import mcp_module.tools.profile  # noqa: F401
```

**Validation:**

```bash
# 1. Server starts
cd backend/app && uvicorn main:app --reload

# 2. tools/list shows profile tools

# 3. Call get_profile → returns authenticated user's profile data

# 4. Call get_goals → returns goals (or empty)

# 5. Frontend still builds
cd ../../frontend/app && npm run build
```

---

### Step 11: MCP Resources

**Goal:** Static/dynamic resources that LLMs can load into context.

**New file:** `backend/app/mcp_module/resources.py`

**Modify:** `backend/app/mcp_module/server.py` — add import

Register resources using the `@mcp_server.resource()` decorator:

| Resource URI | Description |
|-------------|-------------|
| `activities://recent` | Last 20 activities (JSON summary: name, type, date, distance, duration) |
| `health://summary` | Last 30 days of weight, steps, and sleep data |
| `profile://me` | User profile information |

Each resource extracts `user_id` from context and opens its own DB session.

Add import in `mcp_module/server.py`:

```python
import mcp_module.resources  # noqa: F401
```

**Validation:**

```bash
# 1. Server starts
cd backend/app && uvicorn main:app --reload

# 2. List resources
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":5,"method":"resources/list","params":{}}'
# → Shows 3 resources

# 3. Read profile://me → returns user data

# 4. Frontend still builds
cd ../../frontend/app && npm run build
```

---

### Step 12: MCP Prompts

**Goal:** Reusable prompt templates for AI assistants.

**New file:** `backend/app/mcp_module/prompts.py`

**Modify:** `backend/app/mcp_module/server.py` — add import

Register prompts using the `@mcp_server.prompt()` decorator:

| Prompt | Arguments | Description |
|--------|-----------|-------------|
| `analyze_training` | `period: str = "last_30_days"` | Analyze training load, volume, intensity, and recovery |
| `weekly_summary` | (none) | Generate a weekly recap of activities, health metrics, and progress |
| `gear_check` | (none) | Assess gear usage, distance accumulation, suggest maintenance |

Add import in `mcp_module/server.py`:

```python
import mcp_module.prompts  # noqa: F401
```

**Validation:**

```bash
# 1. Server starts
cd backend/app && uvicorn main:app --reload

# 2. List prompts
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":6,"method":"prompts/list","params":{}}'
# → Shows 3 prompts

# 3. Get a prompt → returns structured messages

# 4. Frontend still builds
cd ../../frontend/app && npm run build
```

---

## Phase 3 — End-to-End Validation

### Step 13: Full Integration Test

**Goal:** Verify the complete flow from API key creation to MCP tool usage.

#### Manual test sequence

1. Start backend: `cd backend/app && uvicorn main:app --reload`
2. Start frontend: `cd frontend/app && npm run dev`
3. Log in to the web UI
4. Navigate to Settings > API Keys
5. Create a new API key named "Claude Desktop"
6. Copy the full key
7. Configure Claude Desktop (or any MCP client):
   ```json
   {
     "mcpServers": {
       "endurain": {
         "url": "http://localhost:8000/mcp",
         "headers": {
           "Authorization": "Bearer <paste-key-here>"
         }
       }
     }
   }
   ```
8. In Claude Desktop: verify tools appear in the tools list
9. Ask Claude: "List my recent activities" → should call `list_activities` and return data
10. Ask Claude: "What's my current weight?" → should call `get_weight_data`
11. Ask Claude: "Log my weight as 75.5 kg for today" → should call `log_weight`

#### Security tests

| Test | Expected |
|------|----------|
| Request to `/mcp` without `Authorization` header | 401 |
| Request with invalid/random token | 401 |
| Expired key (manually set `expires_at` in DB to past) | 401 |
| User A's key querying activities | Returns only User A's data |
| User B's key querying activities | Returns only User B's data |

#### Build verification

```bash
# Backend
cd backend && poetry install   # clean
cd app && uvicorn main:app     # starts

# Frontend
cd frontend/app && npm run build   # builds
npm run format                     # passes
```

---

## Phase 4 — Documentation

### Step 14: MCP Integration Docs

**Goal:** Document how users connect MCP clients to Endurain.

**New file:** `docs/integrations/mcp.md`

**Contents:**

1. **What is MCP** — brief explanation
2. **Prerequisites** — running Endurain instance, user account
3. **Generate an API Key** — step-by-step via Settings > API Keys
4. **Configure Claude Desktop** — JSON snippet:
   ```json
   {
     "mcpServers": {
       "endurain": {
         "url": "https://your-endurain.example.com/mcp",
         "headers": { "Authorization": "Bearer <your-api-key>" }
       }
     }
   }
   ```
5. **Configure other MCP clients** — generic HTTP config pattern
6. **Available tools** — table listing all tools with descriptions and parameters
7. **Available resources** — list with URIs
8. **Available prompts** — list with descriptions
9. **Environment variables** — `MCP_ENABLED` toggle
10. **Troubleshooting** — common errors (401, connection refused, etc.)

**Validation:**

```bash
# If mkdocs is configured:
mkdocs serve
# → docs render, all links work, JSON snippets are valid
```

---

## Files Summary

### New files to create (22 files)

| File | Phase | Step |
|------|-------|------|
| `backend/app/api_keys/__init__.py` | 1 | 1 |
| `backend/app/api_keys/models.py` | 1 | 1 |
| `backend/app/api_keys/schema.py` | 1 | 2 |
| `backend/app/api_keys/crud.py` | 1 | 2 |
| `backend/app/api_keys/router.py` | 1 | 2 |
| `backend/app/api_keys/utils.py` | 1 | 3 |
| `frontend/app/src/services/apiKeysService.js` | 1 | 4 |
| `frontend/app/src/components/Settings/SettingsApiKeysZone.vue` | 1 | 4 |
| `backend/app/mcp_module/__init__.py` | 2 | 6 |
| `backend/app/mcp_module/server.py` | 2 | 6 |
| `backend/app/mcp_module/auth.py` | 2 | 6 |
| `backend/app/mcp_module/utils.py` | 2 | 6 |
| `backend/app/mcp_module/tools/__init__.py` | 2 | 7 |
| `backend/app/mcp_module/tools/activities.py` | 2 | 7 |
| `backend/app/mcp_module/tools/health.py` | 2 | 8 |
| `backend/app/mcp_module/tools/gear.py` | 2 | 9 |
| `backend/app/mcp_module/tools/profile.py` | 2 | 10 |
| `backend/app/mcp_module/resources.py` | 2 | 11 |
| `backend/app/mcp_module/prompts.py` | 2 | 12 |
| `backend/app/alembic/versions/<auto>.py` | 1 | 1 |
| `docs/integrations/mcp.md` | 4 | 14 |

### Existing files to modify (7 files)

| File | Change | Step |
|------|--------|------|
| `backend/pyproject.toml` | Add `mcp >= "1.9.0"` dependency | 5 |
| `backend/app/core/config.py` | Add `MCP_ENABLED` env var | 6 |
| `backend/app/core/middleware.py` | Add `/mcp` to CSRF `exempt_path_prefixes` | 6 |
| `backend/app/core/routes.py` | Register `api_keys` router | 2 |
| `backend/app/main.py` | Mount MCP app + session manager lifecycle | 6 |
| `frontend/app/src/components/Settings/SettingsSideBarComponent.vue` | Add "API Keys" nav item | 4 |
| `frontend/app/src/views/SettingsView.vue` | Add `SettingsApiKeysZone` rendering | 4 |
