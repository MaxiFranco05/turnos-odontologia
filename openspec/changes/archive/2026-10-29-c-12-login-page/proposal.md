# Proposal: C-12 Login Page & Mandatory Password Change Flow

## Why

Con el motor de autenticación JWT (`C-03`), el flujo backend de cambio obligatorio de contraseña (`C-04`) y el andamiaje React (`C-11`) ya integrados en `main`, el sistema aún muestra vistas placeholder en `/login` y `/cambiar-password`. Implementar el flujo interactivo de inicio de sesión (`US-001`) y actualización de clave temporal (`US-010`) es el paso crítico en el camino del MVP para conectar el frontend con la API real de autenticación y habilitar la operación de los portales de paciente (`C-13`), recepción (`C-14`) y odontólogo (`C-15`).

## What Changes

- **Página de Inicio de Sesión (`/login`)**: Formulario accesible dentro de `AuthLayout` con campo `identificador` (acepta correo electrónico o N.º de socio/afiliado), `password`, checkbox `"Recordar"` y botón de envío con estado de carga (`loading`).
- **Servicio y Hook de Autenticación (`useLoginMutation`, `useChangePasswordMutation`)**: Integración mediante TanStack Query (`useMutation`, cumpliendo Regla Dura #6 de cero `useEffect` para data fetching) contra `POST /api/auth/login` y `POST /api/auth/cambiar-password`, enviando payloads tipados estrictamente compatibles con `extra="forbid"` del backend.
- **Hidratación y Persistencia de Sesión en `AuthContext`**: Almacenamiento de `access_token` y metadatos de sesión (`rol`, `debe_cambiar_password`, `perfil_completo`, `identificador`) en `localStorage` (o `sessionStorage` cuando `"Recordar"` está desmarcado) con rehidratación automática al recargar la SPA y decodificación segura de claims del JWT (`sub`, `rol`, `debe_cambiar_password`, `perfil_completo`).
- **Redirección Automática por Rol y Estado de Clave**:
  - Si `debe_cambiar_password === true` → redirige obligatoriamente a `/cambiar-password`.
  - Si `debe_cambiar_password === false` → redirige según `rol`: `paciente` → `/paciente/mis-turnos`, `recepcion` → `/recepcion/agenda`, `odontologo` → `/odontologo/agenda`.
- **Manejo Seguro de Errores (`RN-AU-01`)**: Presentación de alerta genérica `"Credenciales inválidas"` ante HTTP `401` (sin revelar si el identificador existe) y mensaje claro de bloqueo temporal ante HTTP `429 Too Many Requests`.
- **Página de Cambio Obligatorio de Contraseña (`/cambiar-password` — `US-010`)**: Formulario interactivo para usuarios con clave temporal (`debe_cambiar_password=true`) que solicita `password_actual`, `password_nueva`, confirmación local de contraseña y, cuando `perfil_completo === false`, campos opcionales/requeridos de completitud de perfil (`nombre`, `email`). Valida política de complejidad (mínimo 8 caracteres, al menos 1 mayúscula y 1 número, distinta a la actual) y actualiza el token JWT al completarse.

## Capabilities

### New Capabilities
- `frontend-auth-flow`: Flujo interactivo de autenticación en cliente (`/login`) con soporte de identificador dual (email o N.º de socio), persistencia configurable de sesión JWT, redirección automática por rol, manejo seguro de errores `401`/`429` (`RN-AU-01`) y pantalla de cambio obligatorio de contraseña temporal (`/cambiar-password`, `US-010`).

### Modified Capabilities
<!-- No spec-level requirement changes to existing capabilities; frontend-application-shell and frontend-api-client already define route guards and 401/403/password_change_required interceptors -->

## Impact

- **Código Frontend**:
  - Nuevas páginas: `frontend/src/pages/LoginPage.tsx` y `frontend/src/pages/CambiarPasswordPage.tsx`.
  - Nuevos servicios/hooks: `frontend/src/services/authService.ts` y `frontend/src/hooks/useAuthMutations.ts`.
  - Actualización de `frontend/src/types/auth.ts`, `frontend/src/context/AuthContext.tsx`, `frontend/src/lib/api.ts` (soporte de almacenamiento dual `localStorage`/`sessionStorage`) y `frontend/src/router/routes.tsx`.
  - Nuevas suites de tests en `frontend/src/pages/LoginPage.test.tsx`, `frontend/src/pages/CambiarPasswordPage.test.tsx` y `frontend/src/services/authService.test.ts`.
- **APIs Consumidas**: `POST /api/auth/login` y `POST /api/auth/cambiar-password` (definidas en `backend/app/api/auth.py`).
