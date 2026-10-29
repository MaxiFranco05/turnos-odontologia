# Design: C-11 Frontend Scaffold

## Context

El proyecto se estructura con una separación limpia entre `backend/` (FastAPI) y `frontend/` (React + TypeScript). 
Para habilitar el desarrollo ágil y desacoplado de las funcionalidades por rol (`C-12` a `C-15`), `C-11` establece la infraestructura base, el cliente de comunicación HTTP, el manejo de sesión JWT en cliente, y el sistema de diseño basado en Tailwind y shadcn/ui.

## Goals / Non-Goals

**Goals:**
- Inicializar el entorno frontend en `frontend/` con Vite, React 18/19, TypeScript (`strict: true`) y Tailwind CSS.
- Proveer un cliente HTTP Axios centralizado con interceptores automáticos para tokens JWT (Bearer), redirección ante 401 y captura de 403.
- Configurar TanStack Query (`QueryClientProvider`) para toda la aplicación.
- Proveer los componentes atómicos base de UI accesibles (Button, Input, Select, Card, Table, Alert, Badge, LoadingSpinner).
- Implementar los cascarones de layouts estructurales (`AuthLayout` para flujos públicos y `AppLayout` con barra de navegación por rol).
- Establecer el pipeline de testing con Vitest y React Testing Library bajo metodología TDD.

**Non-Goals:**
- No implementar el formulario ni el flujo de autenticación contra backend (alcance exclusivo de `C-12 login-page`).
- No implementar las vistas de dominio de los roles (`C-13 patient-features`, `C-14 reception-features`, `C-15 dentist-features`).

## Decisions

### 1. Ubicación y gestión del proyecto Frontend
- **Decisión**: Estructurar en `frontend/` en la raíz del repositorio, con su propio `package.json` y scripts npm (`npm run dev`, `npm run build`, `npm test`).
- **Razón**: Máxima compatibilidad con el entorno de los alumnos y la cátedra, sin requerir herramientas de monorepo complejas (lerna, nx) que introduzcan dependencias ocultas.
- **Alternativa descartada**: `src/frontend` dentro de un monorepo pnpm — descartado para simplificar la reproducibilidad del README según el criterio del TP.

### 2. Sistema de Componentes: Patrón shadcn/ui con Radix Primitives
- **Decisión**: Adoptar el patrón de componentes de shadcn/ui: primitivas sin estilos de Radix UI (`@radix-ui/react-slot`, `@radix-ui/react-select`, etc.) combinadas con Tailwind CSS y utilidades de composición (`clsx`, `tailwind-merge`, `class-variance-authority`).
- **Razón**: Otorga código 100% auditable y modificable en `src/components/ui/`, accesibilidad nativa por teclado y lectores de pantalla (WCAG AA), y cero fricción en los tests de Testing Library.
- **Alternativa descartada**: Ant Design o Material UI — descartados por el peso de su bundle, estilos difíciles de customizar y problemas frecuentes con Vitest/JSDOM.

### 3. Cliente HTTP e Interceptores JWT
- **Decisión**: Centralizar las llamadas en una instancia de Axios (`src/lib/api.ts`).
  - Interceptor Request: Lee el access token de `localStorage` y lo añade en `Authorization: Bearer <token>`.
  - Interceptor Response: Ante `401 Unauthorized`, purga el token almacenado y despacha redirección a `/login`. Ante `403 Forbidden`, emite advertencia de permisos sin cerrar sesión.
- **Razón**: Desacopla a los componentes y hooks de la lógica de autorización.

### 4. Testing Framework: Vitest + React Testing Library
- **Decisión**: Configurar Vitest con entorno `jsdom` y `@testing-library/react`.
- **Razón**: Ejecución ultrarrápida nativa en Vite, compatibilidad con ESM y sintaxis idéntica a Jest, facilitando Strict TDD para cada componente y layout.

## UI Mockups

- **Decision**: no (C-11 establece el scaffold estructural, componentes base y tooling; las maquetas de pantallas completas aplican a los changes de páginas de usuario C-12 a C-15).

## Risks / Trade-offs

- **[Riesgo de CORS en desarrollo local]** → *Mitigación*: Configurar `server.proxy` en `vite.config.ts` para redirigir automáticamente las solicitudes `/api/*` al backend en `http://localhost:8000`.
- **[Riesgo de layout jumps en móviles]** → *Mitigación*: Adoptar `min-h-[100dvh]` y resets de viewport según las directivas de `design-taste-frontend`.
