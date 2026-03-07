# ADR 001: Standardised Health Check Endpoint Contract

## Status

Accepted

## Context

Graphras needs a uniform way to determine whether each service in the
GraphRapids suite is ready before running integration tests against it.
Without a standardised contract, each service would implement readiness
checks differently, making orchestration fragile.

## Decision

All services in the GraphRapids suite **MUST** expose:

| Property | Value |
|---|---|
| Path | `GET /health` |
| Success status | `200 OK` |
| Content-Type | `application/json` |
| Response body | `{"status": "ok"}` |

The response body and status code must not vary between services.  No
authentication is required for the health endpoint.

## Consequences

- Graphras can use a single polling loop for any suite service.
- Docker Compose `healthcheck` blocks and `depends_on` with
  `condition: service_healthy` work uniformly across all services.
- Any deviation from this contract in a future service will require an
  update to this ADR and to the Graphras orchestrator.
