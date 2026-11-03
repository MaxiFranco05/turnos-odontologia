# frontend-auth-flow Specification

## Purpose

Provee el flujo interactivo de inicio de sesión y cambio obligatorio de contraseña temporal en el frontend, gestionando el envío de credenciales duales (correo o N.º de socio), la persistencia configurable del token JWT, la redirección automática según el rol y el manejo seguro de errores de autenticación.

## ADDED Requirements

### Requirement: Dual-identifier login form and role-based redirection
The frontend application MUST provide a `/login` screen accepting either email or membership number (`nro_socio`) as `identificador` along with `password` and a `"Recordar"` preference, authenticating against `POST /api/auth/login` and redirecting the user to their role-specific landing route (`paciente` to `/paciente/mis-turnos`, `recepcion` to `/recepcion/agenda`, `odontologo` to `/odontologo/agenda`) when `debe_cambiar_password` is `false`.

#### Scenario: Inicio de sesión exitoso con redirección por rol y persistencia recordada
- **GIVEN** un usuario en la pantalla `/login` que ingresa un `identificador` válido (correo o N.º de socio), su `password` y marca la casilla `"Recordar"`
- **WHEN** envía el formulario y el backend responde `200 OK` con `debe_cambiar_password=false` y `rol="recepcion"` (o `"odontologo"` / `"paciente"`)
- **THEN** la aplicación almacena el `access_token` y metadatos de sesión en `localStorage`, actualiza el estado de `AuthContext` y redirige automáticamente a `/recepcion/agenda` (o `/odontologo/agenda` / `/paciente/mis-turnos` según corresponda al rol)

#### Scenario: Inicio de sesión sin marcar la casilla Recordar (sesión efímera)
- **GIVEN** un usuario en `/login` que ingresa credenciales válidas y desmarca la casilla `"Recordar"`
- **WHEN** envía el formulario y recibe `200 OK` con `debe_cambiar_password=false`
- **THEN** la aplicación almacena el `access_token` en `sessionStorage` (limpiando cualquier remanente en `localStorage`) e hidrata la sesión activa únicamente para la pestaña actual

#### Scenario: Validación local de campos vacíos antes de enviar a la API
- **GIVEN** un usuario en `/login` que deja vacío el campo `identificador` o `password`
- **WHEN** intenta enviar el formulario
- **THEN** la interfaz muestra mensajes de validación accesibles (`aria-invalid="true"`), impide el disparo de la petición HTTP a `/api/auth/login` y mantiene el foco en el formulario

### Requirement: Generic authentication error and rate-limit feedback
The login interface MUST display a generic `"Credenciales inválidas"` alert on HTTP `401` responses without disclosing whether the identifier exists (`RN-AU-01`), and MUST present a clear rate-limit warning when the server responds with HTTP `429 Too Many Requests`.

#### Scenario: Credenciales incorrectas o usuario inexistente (HTTP 401 — RN-AU-01)
- **GIVEN** un usuario en `/login` que ingresa una combinación de `identificador` y `password` no válida
- **WHEN** el backend responde con código HTTP `401 Unauthorized`
- **THEN** la pantalla muestra una alerta accesible con el texto exacto `"Credenciales inválidas"` sin revelar si falló el usuario o la contraseña, y preserva el valor escrito en `identificador`

#### Scenario: Bloqueo por exceso de intentos fallidos (HTTP 429)
- **GIVEN** un usuario que supera el límite de intentos de inicio de sesión en la ventana de tiempo permitida
- **WHEN** el backend responde con código HTTP `429 Too Many Requests`
- **THEN** la pantalla muestra una alerta indicando que se superó el límite de intentos y que debe aguardar antes de volver a intentar

#### Scenario: Usuario autenticado intenta visitar /login manualmente
- **GIVEN** un usuario que ya posee una sesión activa en `AuthContext` con `debe_cambiar_password=false`
- **WHEN** navega a `/login`
- **THEN** el sistema redirige automáticamente a la ruta de inicio correspondiente a su rol sin mostrar nuevamente el formulario de login

### Requirement: Mandatory temporary password update flow (US-010)
When a user authenticates with `debe_cambiar_password=true`, the system MUST redirect them to `/cambiar-password` and require submitting a valid `password_actual`, a new password (`password_nueva` with at least 8 characters, one uppercase letter, one numeric digit, and different from `password_actual`), and required profile fields (`nombre`, `email`) when `perfil_completo=false` to `POST /api/auth/cambiar-password` before granting access to role routes.

#### Scenario: Cambio obligatorio de contraseña exitoso y redirección al portal del rol
- **GIVEN** un usuario autenticado con `debe_cambiar_password=true` y `perfil_completo=true` en la pantalla `/cambiar-password`
- **WHEN** ingresa su `password_actual`, una `password_nueva` que cumple la política (≥8 caracteres, 1 mayúscula, 1 número, distinta a la actual), su confirmación coincidente y envía el formulario
- **THEN** la aplicación invoca `POST /api/auth/cambiar-password`, reemplaza el token en sesión por el nuevo `access_token` con `debe_cambiar_password=false` y redirige automáticamente al portal del rol del usuario

#### Scenario: Rechazo por incumplimiento de política de contraseña o falta de coincidencia
- **GIVEN** un usuario en `/cambiar-password`
- **WHEN** ingresa una `password_nueva` con menos de 8 caracteres, sin mayúsculas, sin números, igual a `password_actual` o que no coincide con el campo de confirmación
- **THEN** el formulario muestra el error específico de validación en cliente y bloquea el envío HTTP hasta que se corrija

#### Scenario: Paciente con perfil incompleto actualiza clave y completa nombre y email
- **GIVEN** un paciente creado con alta rápida (`debe_cambiar_password=true` y `perfil_completo=false`) en `/cambiar-password`
- **WHEN** el formulario detecta `perfil_completo=false`
- **THEN** exhibe además los campos obligatorios `nombre` y `email`, los incluye en el payload de `POST /api/auth/cambiar-password` y, tras recibir `200 OK`, actualiza `perfil_completo=true` en la sesión
