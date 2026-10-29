# Spec Delta: Frontend API Client

## Purpose

Centraliza el transporte HTTP con la API REST del backend, gestionando la inyección de tokens JWT, el ciclo de vida de la sesión (401/403) y la integración con TanStack Query para fetching asíncrono.

## ADDED Requirements

### Requirement: Automatic JWT bearer authorization
The HTTP client MUST automatically attach the `Authorization: Bearer <token>` header to all outgoing requests to protected API endpoints when an active session token is present.

#### Scenario: Petición saliente con sesión activa
- **GIVEN** un token JWT válido almacenado en el almacenamiento local de sesión
- **WHEN** el cliente HTTP realiza una solicitud a un endpoint protegido (e.g. `/api/turnos`)
- **THEN** la cabecera `Authorization` contiene el esquema `Bearer` con el token exacto

#### Scenario: Petición saliente sin sesión activa
- **GIVEN** que no existe ningún token almacenado en la sesión
- **WHEN** el cliente realiza una solicitud a un endpoint público (e.g. `/api/auth/login`)
- **THEN** la solicitud se envía sin cabecera `Authorization` y no arroja error de cliente antes del envío

### Requirement: Global HTTP authentication and permission handling
The HTTP client MUST intercept HTTP 401 Unauthorized and HTTP 403 Forbidden responses to maintain consistent client session and authorization state.

#### Scenario: Sesión expirada o token inválido (401)
- **GIVEN** una petición realizada con un token expirado o revocado
- **WHEN** la API responde con código HTTP 401
- **THEN** el cliente HTTP elimina las credenciales almacenadas, invalida el estado de usuario y redirige al usuario a `/login`

#### Scenario: Permisos insuficientes para el recurso (403)
- **GIVEN** un usuario autenticado como paciente que intenta consultar un recurso exclusivo de recepción
- **WHEN** la API responde con código HTTP 403
- **THEN** el cliente HTTP emite una notificación de advertencia de "Permisos insuficientes" sin borrar el token de sesión ni cerrar la sesión del usuario

#### Scenario: Falla de red o desconexión del backend (503/Network Error)
- **GIVEN** el servicio de backend no se encuentra disponible o hay una falla de conexión de red
- **WHEN** se dispara una petición HTTP
- **THEN** el interceptor captura la excepción de red y entrega un error estructurado normalizado a los hooks consumidores sin bloquear la UI
