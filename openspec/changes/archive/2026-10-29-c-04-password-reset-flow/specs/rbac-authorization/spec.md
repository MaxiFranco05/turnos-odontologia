# rbac-authorization Specification

## ADDED Requirements

### Requirement: Mandatory Password Change Enforcement on Protected Operations
The system SHALL block access to role-protected operations for any authenticated user whose account still has `debe_cambiar_password=true`, responding with HTTP `403 Forbidden` and `detail: "password_change_required"` (`US-010 CA-2`).

#### Scenario: User with pending password change is blocked from protected operations
- **WHEN** an authenticated user with `debe_cambiar_password=true` requests a role-protected endpoint outside the mandatory password change flow
- **THEN** the system rejects the request with HTTP `403 Forbidden` and `detail` set to `"password_change_required"` without executing the endpoint logic

#### Scenario: User after completing password change is allowed to access protected operations
- **WHEN** an authenticated user whose `debe_cambiar_password` has been set to `false` requests a role-protected endpoint matching their role
- **THEN** the system allows the request and executes the endpoint handler
