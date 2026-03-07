# ADR 002: Dockerised Integration Testing Pattern

## Status

Accepted

## Context

Graphras currently runs only unit tests before pushing a pull request.
Changes that break cross-service contracts are caught only after a PR is
opened, increasing review noise and CI turnaround time.  A pre-push
integration validation step is needed.

## Decision

Each GraphRapids repository adopts the following structure:

1. **Dockerfile** (repo root) — multi-stage build producing a slim,
   production-like image.  No dev dependencies in the final stage.
2. **docker-compose.yml** (repo root) — defines the service and any
   hard dependencies.  Includes a `healthcheck` block so
   `depends_on: condition: service_healthy` works.
3. **`tests/integration/`** — integration tests executed against the
   live service.  Tests are self-contained and idempotent.
4. **Separation from unit tests** — integration tests are skipped
   when the `SERVICE_URL` environment variable is not set, so the
   default test runner only executes unit tests.

The canonical run sequence is:

```bash
docker compose up -d
SERVICE_URL=http://localhost:<port> pytest tests/integration/ -v
docker compose down
```

## Consequences

- Graphras can spin up any service, run its integration tests, and tear
  it down with a uniform script.
- Each repo is self-contained: no shared Docker Compose file is
  required (though one may be introduced later for cross-service tests).
- Developers can run integration tests locally with the same commands.
- CI workflows are **not** changed — this scaffolding is for
  local / Graphras pre-push use only for now.
