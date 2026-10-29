# frontend-application-shell Specification

## MODIFIED Requirements

### Requirement: Role-based SPA layout and routing
The system MUST provide a declarative SPA router with isolated layouts (`AuthLayout` for authentication and mandatory password change flows and `AppLayout` with contextual navigation for patient, receptionist, and dentist roles) and enforce mandatory redirection to `/cambiar-password` when `debe_cambiar_password=true`.

#### Scenario: Acceso de usuario recepcionista a layout privado
- **GIVEN** un usuario autenticado con rol `recepcion`
- **WHEN** navega a la ruta principal del sistema
- **THEN** la aplicación renderiza el `AppLayout` con enlaces a "Agenda del día" y "Plantillas", mostrando el nombre del usuario y botón de cierre de sesión

#### Scenario: Acceso anónimo a ruta protegida
- **GIVEN** un usuario no autenticado (sin token en sesión)
- **WHEN** intenta acceder directamente a una ruta interna (`/recepcion/agenda` o `/paciente/mis-turnos`)
- **THEN** el router intercepta la navegación y redirige inmediatamente al usuario a `/login`

#### Scenario: Usuario con cambio obligatorio de contraseña pendiente
- **GIVEN** un usuario autenticado con `debe_cambiar_password=true`
- **WHEN** intenta navegar a cualquier ruta protegida del sistema fuera de `/cambiar-password`
- **THEN** la guarda de rutas intercepta la navegación y redirige inmediatamente al usuario a `/cambiar-password`

#### Scenario: Usuario con rol no reconocido o sesión corrupta
- **GIVEN** una sesión con un valor de rol inválido o ausente
- **WHEN** el shell intenta calcular la navegación
- **THEN** la aplicación limpia el estado de sesión local y redirige a `/login` mostrando un mensaje de error sin provocar un crash de JavaScript
