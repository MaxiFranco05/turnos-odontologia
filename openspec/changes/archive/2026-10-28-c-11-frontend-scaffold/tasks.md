# Tasks: C-11 Frontend Scaffold

## 1. Tooling e Infraestructura Base

- [x] 1.1 Inicializar la estructura del proyecto en `frontend/` con Vite, React, TypeScript (`strict: true`) y verificar que `package.json` y `tsconfig.json` compilen limpiamente.
- [x] 1.2 Configurar Tailwind CSS, PostCSS y el helper `cn` (`clsx` + `tailwind-merge`) y verificar que los estilos procesen sin errores.
- [x] 1.3 Configurar Vitest con entorno `jsdom`, `@testing-library/react` y `@testing-library/jest-dom`, verificando la ejecución del comando `npm test`.

## 2. Cliente HTTP y Networking (Strict TDD)

- [x] 2.1 Escribir pruebas unitarias en `src/lib/api.test.ts` para verificar la inyección automática del token `Bearer` cuando existe sesión y su omisión en llamadas anónimas.
- [x] 2.2 Implementar la instancia de Axios e interceptor de request en `src/lib/api.ts` hasta lograr test verde.
- [x] 2.3 Escribir pruebas unitarias para interceptores de respuesta: redirección a `/login` ante HTTP 401 y notificación de permisos ante HTTP 403.
- [x] 2.4 Implementar los interceptores de respuesta en `src/lib/api.ts` satisfaciendo todas las aserciones de error y sesión.
- [x] 2.5 Configurar `QueryClient` de TanStack Query y su proveedor global en `src/lib/queryClient.ts`.

## 3. Catálogo de Componentes UI Base (shadcn/ui Pattern)

- [x] 3.1 Escribir tests y componente para `Button` (variantes default, outline, destructive, estado disabled y estado loading accesible) en `src/components/ui/Button.tsx`.
- [x] 3.2 Escribir tests y componente para `Input` (etiquetado accesible, soporte de `aria-invalid` y mensaje de error) en `src/components/ui/Input.tsx`.
- [x] 3.3 Implementar componentes base `Card`, `Badge` (estados de turnos), `Alert` y `Table` con soporte para tipografía tabular odontológica en `src/components/ui/`.

## 4. Layouts y Enrutador SPA

- [x] 4.1 Escribir tests de renderizado para `AppLayout` verificando que muestre la navegación correspondiente según el rol del usuario (`recepcion`, `odontologo`, `paciente`).
- [x] 4.2 Implementar `AuthLayout` (público) y `AppLayout` (privado con header de usuario, sidebar colapsable y botón de logout) en `src/layouts/`.
- [x] 4.3 Configurar React Router en `src/router/routes.tsx` integrando guardas de autenticación y layouts por rol.
- [x] 4.4 Ejecutar suite completa de tests de frontend y verificar 100% de tests en verde junto con `npm run build` exitoso.

## Workflow follow-up

- Presentar propuesta, especificaciones delta y tareas al usuario para inspección y aprobación antes de iniciar la fase Apply.
