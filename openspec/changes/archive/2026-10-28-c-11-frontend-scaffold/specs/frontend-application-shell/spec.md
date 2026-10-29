# Spec Delta: Frontend Application Shell

## Purpose

Provee el shell y runtime de la aplicación SPA en React con enrutamiento protegido por roles, layouts adaptativos (AuthLayout y AppLayout) y catálogo de componentes UI accesibles para la gestión odontológica.

## ADDED Requirements

### Requirement: Role-based SPA layout and routing
The system MUST provide a declarative SPA router with isolated layouts (`AuthLayout` for authentication flows and `AppLayout` with contextual navigation for patient, receptionist, and dentist roles).

#### Scenario: Acceso de usuario recepcionista a layout privado
- **GIVEN** un usuario autenticado con rol `recepcion`
- **WHEN** navega a la ruta principal del sistema
- **THEN** la aplicación renderiza el `AppLayout` con enlaces a "Agenda del día" y "Plantillas", mostrando el nombre del usuario y botón de cierre de sesión

#### Scenario: Acceso anónimo a ruta protegida
- **GIVEN** un usuario no autenticado (sin token en sesión)
- **WHEN** intenta acceder directamente a una ruta interna (`/recepcion/agenda` o `/paciente/mis-turnos`)
- **THEN** el router intercepta la navegación y redirige inmediatamente al usuario a `/login`

#### Scenario: Usuario con rol no reconocido o sesión corrupta
- **GIVEN** una sesión con un valor de rol inválido o ausente
- **WHEN** el shell intenta calcular la navegación
- **THEN** la aplicación limpia el estado de sesión local y redirige a `/login` mostrando un mensaje de error sin provocar un crash de JavaScript

### Requirement: Accessible base UI components
The frontend application MUST supply an accessible base UI component catalog (Button, Input, Select, Card, Table, Alert, LoadingSpinner) fully compliant with keyboard navigation and screen readers.

#### Scenario: Estado de carga en componente Button
- **GIVEN** un componente Button configurado con propiedad `loading=true`
- **WHEN** el usuario hace clic o presiona Enter sobre el botón
- **THEN** el botón muestra el indicador visual de carga, se deshabilita para evitar dobles clics y no dispara el evento `onClick`

#### Scenario: Campo de formulario con mensaje de error accesible
- **GIVEN** un componente Input con una propiedad de error activa
- **WHEN** se renderiza en la pantalla
- **THEN** el campo expone visualmente el mensaje de error con contraste legible y asocia el mensaje mediante `aria-describedby` e `aria-invalid=true`
