# Tasks: C-12 Login Page & Mandatory Password Change Flow

## 1. Tipos, Servicio de Autenticación y Persistencia de Sesión (Strict TDD)

- [x] 1.1 Extender `frontend/src/types/auth.ts` con los contratos estrictos `LoginRequestPayload`, `ChangePasswordRequestPayload`, `TokenResponsePayload` y el helper `getDefaultRouteForUser(user)` (sin `any`), verificando compilación limpia con `tsc --noEmit`.
- [x] 1.2 Escribir pruebas unitarias (RED) en `frontend/src/services/authService.test.ts` para `loginUser`, `changePassword`, persistencia dual (`localStorage` vs `sessionStorage` según `"Recordar"`) y decodificación de claims JWT (`sub`, `rol`, `debe_cambiar_password`, `perfil_completo`).
- [x] 1.3 Implementar `frontend/src/services/authService.ts`, actualizar `setAuthToken`/`getAuthToken`/`clearAuthToken` en `frontend/src/lib/api.ts` e hidratar `AuthContext` (`frontend/src/context/AuthContext.tsx`) con soporte de `establishSession(tokenResponse, identifier, remember)` hasta pasar todas las pruebas de `authService.test.ts` (GREEN + REFACTOR).
- [x] 1.4 Implementar los hooks `useLoginMutation` y `useChangePasswordMutation` con `useMutation` de TanStack Query en `frontend/src/hooks/useAuthMutations.ts` (sin `useEffect`), verificando que actualicen `AuthContext` al completarse.

## 2. Página de Inicio de Sesión `/login` (Strict TDD)

- [x] 2.1 Escribir pruebas de componente e integración (RED) en `frontend/src/pages/LoginPage.test.tsx` cubriendo: renderizado accesible de `identificador`, `password` y checkbox `"Recordar"`; validación de campos vacíos; login exitoso con redirección a `/recepcion/agenda`, `/odontologo/agenda` o `/paciente/mis-turnos`; redirección a `/cambiar-password` cuando `debe_cambiar_password=true`; alerta genérica `"Credenciales inválidas"` en HTTP `401` (`RN-AU-01`); y alerta de límite de intentos en HTTP `429`.
- [x] 2.2 Implementar el componente `LoginPage` en `frontend/src/pages/LoginPage.tsx` (en `PascalCase`, usando `Input`, `Button`, `Alert` y `useLoginMutation`) hasta lograr 100% de tests en verde en `LoginPage.test.tsx` (GREEN + REFACTOR).

## 3. Página de Cambio Obligatorio de Contraseña `/cambiar-password` — US-010 (Strict TDD)

- [x] 3.1 Escribir pruebas de componente e integración (RED) en `frontend/src/pages/CambiarPasswordPage.test.tsx` cubriendo: bloqueo de envío ante incumplimiento de política (menos de 8 caracteres, sin mayúscula, sin número, igual a la actual o confirmación distinta); exhibición condicional de `nombre` y `email` cuando `perfil_completo=false`; envío estricto sin campos extra (`extra="forbid"`) a `POST /api/auth/cambiar-password`; y actualización de sesión + redirección al portal del rol tras recibir `200 OK`.
- [x] 3.2 Implementar el componente `CambiarPasswordPage` en `frontend/src/pages/CambiarPasswordPage.tsx` hasta pasar todas las pruebas de `CambiarPasswordPage.test.tsx` (GREEN + REFACTOR).

## 4. Integración en Router y Verificación Integral

- [x] 4.1 Conectar `LoginPage` en la ruta `/login` y `CambiarPasswordPage` en `/cambiar-password` dentro de `frontend/src/router/routes.tsx`, actualizando las pruebas de enrutamiento para verificar la navegación completa entre `/login`, `/cambiar-password` y las rutas protegidas por rol.
- [x] 4.2 Ejecutar la suite completa de tests de frontend (`npm test -- --run`) y el build de producción (`npm run build`), verificando 100% de pruebas en verde y cero errores de TypeScript.

## Workflow follow-up

- Presentar los artefactos de planificación (`proposal.md`, `specs/frontend-auth-flow/spec.md`, `design.md`, `tasks.md`) al usuario y aguardar confirmación antes de ejecutar `/opsx-apply`.
- Una vez implementado y verificado en la fase Apply, archivar el change con `/opsx-archive` y marcar `[x]` `C-12` en `CHANGES.md`.
