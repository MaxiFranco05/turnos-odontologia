# frontend-api-client Specification

## MODIFIED Requirements

### Requirement: Global HTTP authentication and permission handling
The HTTP client MUST intercept HTTP 401 Unauthorized, HTTP 403 Forbidden, and HTTP 400/403 `"password_change_required"` responses to maintain consistent client session, mandatory password change redirection, and authorization state.

#### Scenario: Sesión expirada o token inválido (401)
- **GIVEN** una petición realizada con un token expirado o revocado
- **WHEN** la API responde con código HTTP 401
- **THEN** el cliente HTTP elimina las credenciales almacenadas, invalida el estado de usuario y redirige al usuario a `/login`

#### Scenario: Permisos insuficientes para el recurso (403)
- **GIVEN** un usuario autenticado como paciente que intenta consultar un recurso exclusivo de recepción
- **WHEN** la API responde con código HTTP 403
- **THEN** el cliente HTTP emite una notificación de advertencia de "Permisos insuficientes" sin borrar el token de sesión ni cerrar la sesión del usuario

#### Scenario: Cambio obligatorio de contraseña requerido (403/400 password_change_required)
- **GIVEN** un usuario autenticado con contraseña temporal (`debe_cambiar_password=true`) que realiza una petición a la API
- **WHEN** la API responde con HTTP 403 o 400 y detalle `"password_change_required"`
- **THEN** el cliente HTTP preserva el token JWT activo y redirige al usuario a `/cambiar-password` (o invoca el handler de cambio obligatorio) sin disparar la alerta genérica de permisos insuficientes

#### Scenario: Falla de red o desconexión del backend (503/Network Error)
- **GIVEN** el servicio de backend no se encuentra disponible o hay una falla de conexión de red
- **WHEN** se dispara una petición HTTP
- **THEN** el interceptor captura la excepción de red y entrega un error estructurado normalizado a los hooks consumidores sin bloquear la UI
