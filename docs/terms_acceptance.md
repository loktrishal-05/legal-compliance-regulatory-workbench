# Terms acceptance API for frontend integration

UI API commit `11fdd1c` is already integrated on main as `831c149` (identical patch).
No frontend visuals or AI safety/governance rules change here.

## Version and storage

`CURRENT_TERMS_VERSION=1.0` is the default backend configuration. Deploy the same
value to every backend worker. Change it together with the published terms and
acknowledgement text; all users, including admins, must explicitly accept again.
Do not reuse a version for changed terms. Acceptance is never inferred from login,
a GET, an existing account, or continued use.

Migration `0018_terms_acceptance` follows unchanged `0017_accounts_recovery`.
Existing users start unaccepted. The user row stores the latest terms version,
UTC acceptance timestamp, and bounded ASGI peer host (IP/hostname if available).
The existing user ID binds the receipt. No user agent, location, forwarded header,
reverse-DNS lookup, or additional personal information is collected.
Prior version receipts remain in `TERMS_ACCEPTED` audit events. Each contains
the authenticated actor ID, version, timestamp, peer host and four true flags.
The acceptance update and mandatory audit append commit atomically. Duplicate
submissions preserve the original timestamp/event; PostgreSQL serializes them by
locking the user row. Downgrade refuses to destroy acceptance history.

## Exact contract

Both endpoints require the existing HttpOnly session cookie and send `Cache-Control:
no-store`. Use `credentials: "include"`; mutation origin checks match other auth APIs.

`GET /auth/terms/current`:

```json
{
  "version": "1.0",
  "requires_acceptance": true,
  "accepted_at": null,
  "acknowledgements": [
    {"id": "advisory_only", "text": "I understand AI outputs are advisory only and must be independently verified."},
    {"id": "no_equipment_control", "text": "I understand the AI cannot control plant equipment."},
    {"id": "no_bypass", "text": "I will not attempt to bypass safety, access or audit controls."},
    {"id": "audit_logging", "text": "I understand my application activity is recorded in the tamper-evident audit log."}
  ]
}
```

When accepted for the current version, `requires_acceptance` is false and
`accepted_at` is an ISO 8601 UTC timestamp. Older-version acceptance returns null
here; its historical receipt remains in the audit chain.

`POST /auth/terms/accept`:

```json
{
  "version": "1.0",
  "acknowledgements": {
    "advisory_only": true,
    "no_equipment_control": true,
    "no_bypass": true,
    "audit_logging": true
  }
}
```

Success (200): `{"version":"1.0","accepted_at":"<UTC timestamp>"}`.
Every field is required; booleans must literally be true. Unknown fields,
including `user_id`, are rejected (422). No account identity is supplied by the
client. A stale/unknown version returns 409 with
`{"detail":{"code":"terms_version_changed","version":"<current>"}}`.
Unauthenticated, expired or revoked sessions return 401. Disallowed origins return 403.

## Gate and Claude frontend handoff

After login (including Google callback), and when restoring a session, fetch
`/auth/terms/current`. Keep Workbench data requests/actions disabled until accepted.
Render the supplied terms v1.0 document and the exact four returned acknowledgement
texts with initially unchecked controls. Submit only after all are checked.
On 409, refetch the version and require fresh checks. Logout remains available.

The shared cookie-auth dependency enforces this on protected APIs regardless of
frontend state, role, or manually opening `/app/...`. It returns 403 with
`{"detail":{"code":"terms_acceptance_required","version":"<current>"}}`.
Handle this response anywhere by returning to acceptance. A static SPA URL itself
does not grant access to backend data; this backend change does not add or redesign
a frontend acceptance screen.

`/auth/me`, `/auth/sessions` and its revocation endpoints, terms status/acceptance,
logout and existing login/recovery flows remain available. Public health/runtime
probes retain their existing behavior; they grant no protected Workbench access.
Admin APIs are gated. Session revocation, RBAC and governance checks still apply
after acceptance. The new session-only dependency is reserved for auth/terms routes.

## Validation

Run the terms, auth, UI API, PostgreSQL and existing HTTP authorization tests,
then the full Linux backend suite with `WORKBENCH_TEST_POSTGRES=1`, Alembic upgrade
and check, and `python -m scripts.frozen_integrity`. BLIND must not execute.
Terms tests cover real cookies, strict input, per-account/version binding, origin
checks, persisted acceptance, gate bypass attempts, atomic audit failure, and
PostgreSQL upgrade/downgrade/concurrent acceptance behavior.
