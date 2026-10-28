# health-monitoring Specification

## Purpose

Exposes standard HTTP health check endpoints for container orchestrators and monitoring tools to determine process liveness and transactional dependency readiness.

## Requirements

### Requirement: Liveness probe
The system SHALL expose an HTTP liveness endpoint at `/health/live` that immediately confirms process availability.

#### Scenario: Process is active
- **WHEN** a client or orchestrator performs an HTTP GET request to `/health/live`
- **THEN** the system returns HTTP status 200 with status payload `{"status": "alive"}`

### Requirement: Readiness probe with database connectivity check
The system SHALL expose an HTTP readiness endpoint at `/health/ready` that verifies live database responsiveness and reports failure when the database is unavailable.

#### Scenario: Database is responsive
- **WHEN** a client performs an HTTP GET request to `/health/ready` and the database responds to connectivity probes
- **THEN** the system returns HTTP status 200 with status payload `{"status": "ready", "database": "connected"}`

#### Scenario: Database is unreachable or timing out
- **WHEN** a client performs an HTTP GET request to `/health/ready` and database connection fails or times out
- **THEN** the system returns HTTP status 503 Service Unavailable with payload detailing database degradation
