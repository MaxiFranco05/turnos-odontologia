# password-reset-flow Specification

## Purpose

Enables newly provisioned accounts with temporary passwords (`debe_cambiar_password=true`) to complete their mandatory first-login password change, validating current credentials and password strength while updating account activation and profile completeness state (`US-010`).

## Requirements

### Requirement: Mandatory First-Time Password Replacement
The system SHALL allow an authenticated user with `debe_cambiar_password=true` to replace their temporary password via `POST /api/auth/cambiar-password` by providing their current password and a compliant new password, clearing `debe_cambiar_password` to `false` and returning an updated access token.

#### Scenario: Successful first-time password change
- **WHEN** an authenticated user with `debe_cambiar_password=true` submits `POST /api/auth/cambiar-password` with their valid `password_actual` and a valid `password_nueva`
- **THEN** the system updates the user's stored password hash, sets `debe_cambiar_password` to `false`, and responds with HTTP `200 OK` containing a fresh `access_token` with `debe_cambiar_password=false`

#### Scenario: Reject password change when flag is already false
- **WHEN** an authenticated user with `debe_cambiar_password=false` submits `POST /api/auth/cambiar-password`
- **THEN** the system rejects the request with HTTP `400 Bad Request` without modifying the user's password

#### Scenario: Reject password change when current password does not match
- **WHEN** an authenticated user with `debe_cambiar_password=true` submits `POST /api/auth/cambiar-password` with an incorrect `password_actual`
- **THEN** the system rejects the request with HTTP `400 Bad Request` and leaves `debe_cambiar_password` set to `true`

### Requirement: Password Strength Enforcement
The system SHALL require `password_nueva` to have at least 8 characters, at least one uppercase letter, at least one numeric digit, and to differ from `password_actual`.

#### Scenario: Password shorter than 8 characters is rejected
- **WHEN** an authenticated user submits `POST /api/auth/cambiar-password` with a `password_nueva` shorter than 8 characters
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` (or `400 Bad Request`) and keeps `debe_cambiar_password=true`

#### Scenario: Password missing uppercase letter or digit is rejected
- **WHEN** an authenticated user submits `POST /api/auth/cambiar-password` with a `password_nueva` lacking an uppercase letter or lacking a digit
- **THEN** the system rejects the request with HTTP `422 Unprocessable Entity` (or `400 Bad Request`) and keeps `debe_cambiar_password=true`

#### Scenario: New password identical to current password is rejected
- **WHEN** an authenticated user submits `POST /api/auth/cambiar-password` where `password_nueva` equals `password_actual`
- **THEN** the system rejects the request with HTTP `400 Bad Request` and keeps `debe_cambiar_password=true`

### Requirement: Profile Completeness Evaluation on Password Change
The system SHALL update `perfil_completo` to `true` upon completing the mandatory password change when the user's minimum profile fields (`nombre` non-empty and `email` present) are populated (`US-010 CA-3`).

#### Scenario: Profile marked complete when minimum data are present
- **WHEN** an authenticated user with `debe_cambiar_password=true` completes `POST /api/auth/cambiar-password` and the account has non-empty `nombre` and `email` (either pre-existing or supplied in the request)
- **THEN** the system sets `perfil_completo` to `true` alongside `debe_cambiar_password=false`

#### Scenario: Profile remains incomplete if email is still absent
- **WHEN** an authenticated patient authenticated only by `nro_socio` (with `email=null`) completes `POST /api/auth/cambiar-password` without providing an `email`
- **THEN** the system sets `debe_cambiar_password` to `false` while keeping `perfil_completo` set to `false`
