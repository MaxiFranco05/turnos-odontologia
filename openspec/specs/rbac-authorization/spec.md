# rbac-authorization Specification

## Purpose

Enforces server-side authentication and role-based access control (RBAC) across protected API endpoints by validating Bearer JWT tokens, resolving the active user into the request context, and restricting endpoint access by role (`paciente`, `recepcion`, `odontologo`).

## Requirements

### Requirement: Bearer Token Authentication and User Context Resolution
The system SHALL validate the `Authorization: Bearer <token>` header on protected endpoints, resolve the corresponding user from persistent storage, and attach the authenticated user to the request state.

#### Scenario: Valid Bearer token resolves authenticated user
- **WHEN** a client requests a protected endpoint with a valid, non-expired Bearer token whose `sub` matches an existing user ID
- **THEN** the system resolves the user entity, attaches it to the request state, and allows the request to proceed

#### Scenario: Missing or malformed Authorization header is rejected
- **WHEN** a client requests a protected endpoint without an `Authorization: Bearer <token>` header or with a malformed token
- **THEN** the system rejects the request with HTTP `401 Unauthorized`

#### Scenario: Expired JWT token is rejected
- **WHEN** a client requests a protected endpoint with a Bearer token whose `exp` timestamp is in the past
- **THEN** the system rejects the request with HTTP `401 Unauthorized`

#### Scenario: Token referencing a non-existent user is rejected
- **WHEN** a client requests a protected endpoint with a cryptographically valid Bearer token whose `sub` does not match any existing user
- **THEN** the system rejects the request with HTTP `401 Unauthorized`

### Requirement: Role-Based Endpoint Access Control
The system SHALL enforce role restrictions on protected endpoints (`RN-AU-02`, `RN-GL-01`) and reject authenticated users whose role is not in the endpoint's permitted role set with HTTP `403 Forbidden`.

#### Scenario: User with permitted role accesses protected endpoint
- **WHEN** an authenticated user whose role is included in the endpoint's allowed roles requests the endpoint
- **THEN** the system authorizes the request and executes the endpoint handler

#### Scenario: User with unpermitted role is rejected with 403
- **WHEN** an authenticated user with role `paciente` requests an endpoint restricted to `recepcion` or `odontologo`
- **THEN** the system rejects the request with HTTP `403 Forbidden` without executing the endpoint's business logic
