# jwt-authentication Specification

## Purpose

Provides credential-based user authentication via email or membership number (`nro_socio`) and password, issuing signed JSON Web Tokens (JWT) with role and password-change metadata while protecting the login endpoint against brute-force attempts.

## ADDED Requirements

### Requirement: Login with Email or Membership Number
The system SHALL authenticate users via `POST /api/auth/login` accepting an identifier (`identificador`, matching either `email` or `nro_socio`) and a `password`, and return a signed JWT access token along with the user's role and `debe_cambiar_password` status.

#### Scenario: Successful login using email
- **WHEN** a registered user submits a `POST /api/auth/login` request with their valid `email` as `identificador` and matching `password`
- **THEN** the system responds with HTTP `200 OK` containing `access_token`, `token_type` set to `"bearer"`, `rol`, and `debe_cambiar_password`

#### Scenario: Successful login using membership number
- **WHEN** a registered patient submits a `POST /api/auth/login` request with their valid `nro_socio` as `identificador` and matching `password`
- **THEN** the system responds with HTTP `200 OK` containing `access_token`, `token_type` set to `"bearer"`, `rol` set to `"paciente"`, and `debe_cambiar_password`

### Requirement: JWT Claims and Expiration Contract
The system SHALL issue JWT access tokens containing the `sub` claim (stringified user ID), `rol` claim, `debe_cambiar_password` claim, and `exp` claim calculated from the configured token expiration duration.

#### Scenario: Issued token contains required claims and expiration
- **WHEN** a user authenticates successfully at `POST /api/auth/login`
- **THEN** the decoded `access_token` payload contains `sub` equal to the user's ID string, `rol` equal to the user's role, `debe_cambiar_password` matching the user's account state, and `exp` set to the current UTC timestamp plus the configured expiration minutes

### Requirement: Generic Error on Invalid Credentials
The system SHALL reject invalid login attempts with HTTP `401 Unauthorized` and a single generic error message without disclosing whether the identifier exists or the password was incorrect (`RN-AU-01`).

#### Scenario: Login attempt with non-existent identifier
- **WHEN** a client submits `POST /api/auth/login` with an `identificador` that does not match any user's `email` or `nro_socio`
- **THEN** the system responds with HTTP `401 Unauthorized` and detail `"Credenciales inválidas"`

#### Scenario: Login attempt with wrong password
- **WHEN** a client submits `POST /api/auth/login` with a valid `identificador` but an incorrect `password`
- **THEN** the system responds with HTTP `401 Unauthorized` and the exact same detail `"Credenciales inválidas"`

### Requirement: Strict Login Request Validation
The system SHALL reject login payloads that omit required fields or include undeclared fields.

#### Scenario: Login payload with extra undeclared fields
- **WHEN** a client submits `POST /api/auth/login` containing an undeclared JSON field in the request body
- **THEN** the system responds with HTTP `422 Unprocessable Entity`

### Requirement: Login Brute-Force Rate Limiting
The system SHALL limit login attempts on `POST /api/auth/login` to at most 5 requests per 60-second window for each `(client_ip, identificador)` pair.

#### Scenario: Rate limit exceeded for the same IP and identifier
- **WHEN** a client from the same IP address sends a 6th `POST /api/auth/login` request with the same `identificador` within 60 seconds
- **THEN** the system rejects the request with HTTP `429 Too Many Requests` without evaluating credentials

#### Scenario: Different identifier from the same IP is not blocked
- **WHEN** a client from the same IP address has reached 5 requests for identifier A within 60 seconds and sends a login request for identifier B
- **THEN** the system processes the request for identifier B normally
