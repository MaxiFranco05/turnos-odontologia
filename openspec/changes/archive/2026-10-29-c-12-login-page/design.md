# Design: C-12 Login Page & Mandatory Password Change Flow

## Context

El backend ya expone en `main` los endpoints definitivos de autenticación (`C-03` y `C-04` en `backend/app/api/auth.py`):
- `POST /api/auth/login`: recibe `LoginRequest` (`{ identificador: string, password: string }`, con `extra="forbid"`) y devuelve `TokenResponse` (`{ access_token, token_type, rol, debe_cambiar_password, perfil_completo }`).
- `POST /api/auth/cambiar-password`: recibe `ChangePasswordRequest` (`{ password_actual, password_nueva, nombre?: string | null, email?: string | null }`, con `extra="forbid"`) y devuelve un nuevo `TokenResponse` con `debe_cambiar_password: false`.

Por su parte, el frontend (`C-11`) ya cuenta con `AuthLayout`, `AppLayout`, `ProtectedRoute`, cliente Axios (`src/lib/api.ts`) con interceptores `401`/`403`/`password_change_required`, y `AuthContext` (`src/context/AuthContext.tsx`). Falta conectar las pantallas reales `/login` y `/cambiar-password`, hidratar la sesión desde el token JWT persistido y manejar las mutaciones HTTP sin `useEffect`.

Ver `proposal.md` para la motivación de negocio y el alcance del change.

## Goals / Non-Goals

**Goals:**
- Implementar `LoginPage` (`/login`) y `CambiarPasswordPage` (`/cambiar-password`) con componentes accesibles de `src/components/ui/` (`Card`, `Input`, `Button`, `Alert`).
- Ejecutar todas las operaciones de autenticación mediante `useMutation` de TanStack Query (cumpliendo la Regla Dura #6: prohibido `useEffect` para data fetching).
- Soportar persistencia dual del token (`localStorage` cuando `"Recordar"` está activo; `sessionStorage` cuando está desmarcado) e hidratación sincrónica inicial en `AuthContext` decodificando el payload base64url del JWT.
- Garantizar cumplimiento estricto de `extra="forbid"` del backend enviando únicamente las propiedades declaradas en cada DTO.
- Preservar la compatibilidad con el `DevToolbar` (Simulador de Roles de desarrollo) para no romper pruebas ni inspección manual de otros roles.

**Non-Goals:**
- No implementar recuperación de contraseña por correo externo (no existe servidor SMTP en v1 según KB; el blanqueo lo realiza Recepción con clave temporal según `C-04`).
- No implementar las pantallas internas de cada rol (`C-13`, `C-14`, `C-15`).

## Decisions

### 1. Mutaciones con TanStack Query (`useMutation`) en lugar de `useEffect` / estado manual de promesa
- **Decisión**: Encapsular las llamadas a `POST /api/auth/login` y `POST /api/auth/cambiar-password` en funciones puras dentro de `src/services/authService.ts` y exponerlas mediante hooks `useLoginMutation` y `useChangePasswordMutation` basados en `useMutation` (`@tanstack/react-query`).
- **Razón**: Cumple la Regla Dura #6, provee estados `isPending`, `error` y `reset` libres de condiciones de carrera y evita fugas de memoria si el componente se desmonta durante la redirección.
- **Alternativa descartada**: Llamar a `apiClient.post` con `useState(loading)` manual dentro del handler — descartado por verbosidad y menor estandarización con el resto de los changes (`C-13` a `C-15`).

### 2. Persistencia Dual (`localStorage` vs `sessionStorage`) e Hidratación desde JWT
- **Decisión**: Extender `setAuthToken(token, remember = true)` y `getAuthToken()` en `src/lib/api.ts` para buscar primero en `localStorage` y luego en `sessionStorage`, junto con almacenamiento de metadatos de sesión (`auth_session_meta`) o decodificación base64url del payload JWT (`sub`, `rol`, `debe_cambiar_password`, `perfil_completo`).
- **Razón**: Permite que el checkbox `"Recordar"` tenga un efecto real y verificable (persistir entre cierres de navegador vs. vivir solo en la pestaña actual) y asegura que al refrescar la página (`F5`) `AuthContext` reconstruya `user` sincrónicamente en el estado inicial de `useState(() => loadInitialSession())` sin parpadeos ni redirecciones falsas a `/login`.
- **Alternativa descartada**: Llamar a un endpoint `/api/auth/me` dentro de un `useEffect` al montar `AuthProvider` — descartado porque dicho endpoint no existe en `backend/app/api/auth.py` y además violaría la Regla Dura #6.

### 3. Redirección Declarativa Post-Login y Guarda Inversa en `/login`
- **Decisión**: Centralizar el mapa de rutas por defecto en un helper `getDefaultRouteForUser(user: UserProfile): string`:
  - Si `user.debe_cambiar_password === true` → `'/cambiar-password'`
  - Si `user.rol === 'recepcion'` → `'/recepcion/agenda'`
  - Si `user.rol === 'odontologo'` → `'/odontologo/agenda'`
  - Si `user.rol === 'paciente'` → `'/paciente/mis-turnos'`
  Además, si `LoginPage` detecta un `user` ya autenticado en `AuthContext`, renderiza `<Navigate to={getDefaultRouteForUser(user)} replace />`.
- **Razón**: Evita duplicar la tabla de ruteo entre `LoginPage`, `CambiarPasswordPage`, `ProtectedRoute` y `DevToolbar`.

### 4. Validación de Política de Contraseña en Cliente + Servidor en `/cambiar-password`
- **Decisión**: Validar en cliente antes del submit las mismas reglas de `ChangePasswordRequest` del backend (`len >= 8`, `/[A-Z]/`, `/\d/`, `password_nueva !== password_actual`, y `password_nueva === confirmar_password`), pero sin enviar `confirmar_password` en el JSON hacia `POST /api/auth/cambiar-password`.
- **Razón**: El backend tiene `extra="forbid"` en `ChangePasswordRequest` (Regla Dura #1); enviar un campo `confirmar_password` causaría un `422 Unprocessable Entity`. La confirmación se valida en cliente y el payload enviado contiene estrictamente `{ password_actual, password_nueva, ...(nombre ? { nombre } : {}), ...(email ? { email } : {}) }`.

## UI Mockups

- **Decision**: no (project policy / continuación directa del sistema de componentes clínicos shadcn/ui establecido en `C-11`, utilizando `AuthLayout` ya aprobado y verificado en el repositorio).

## Risks / Trade-offs

- **[Riesgo de Error 422 por `extra="forbid"` en FastAPI]** → *Mitigación*: Construir objetos de request explícitos en `authService.ts` (`{ identificador: identificador.trim(), password }`) y verificar en tests unitarios el cuerpo exacto enviado a Axios.
- **[Riesgo de Bucle de Redirección entre `/login`, `/cambiar-password` y `ProtectedRoute`]** → *Mitigación*:
  - `/login` redirige a `/cambiar-password` cuando `user.debe_cambiar_password === true`.
  - `/cambiar-password` redirige a `/login` si `user === null`, o a la ruta del rol si `user.debe_cambiar_password === false`.
  - `ProtectedRoute` redirige a `/cambiar-password` cuando `user.debe_cambiar_password === true`.
  Cubrir los 3 estados con tests de integración de enrutamiento en Vitest.
