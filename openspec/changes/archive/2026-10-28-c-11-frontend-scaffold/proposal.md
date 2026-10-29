# Proposal: C-11 Frontend Scaffold

## Why

El backend cuenta con la fundación modular ASGI (`C-01`) y el modelo relacional core (`C-02`), pero el proyecto carece de una interfaz de usuario interactiva y de una infraestructura frontend ejecutable. 
Para que los pacientes, recepcionistas y odontólogos puedan operar el sistema de turnos, y para habilitar el desarrollo independiente de las vistas de cada rol (`C-12` a `C-15`), es indispensable establecer el andamiaje del frontend: arquitectura de componentes, cliente HTTP con interceptores JWT, routing por roles y biblioteca de componentes UI accesible y consistente con el diseño clínico.

## What Changes

- **Estructura y Tooling Frontend**: Configuración de aplicación SPA con Vite + React 18/19 + TypeScript (`strict: true`) en `frontend/`, junto con Tailwind CSS y tipografía legible con espaciado clínico.
- **Sistema de Componentes UI Base (shadcn/ui pattern)**: Primitivas accesibles basadas en Radix UI y Tailwind: `Button`, `Input`, `Select`, `Card`, `Table`, `Toast/Alert`, `Skeleton/LoadingSpinner`.
- **Cliente API & Networking**: Cliente Axios configurado con base URL `/api` (proxied a backend en desarrollo), interceptor para adjuntar token JWT Bearer, manejo de error `401` (redirección a login) y `403` (feedback de acceso no autorizado).
- **Gestión de Estado Servidor**: Configuración del `QueryClientProvider` de TanStack Query para fetching, cache y revalidación sin `useEffect`.
- **Layouts y Enrutamiento**: Configuración de React Router con `AuthLayout` (vistas públicas de autenticación) y `AppLayout` (sidebar por rol `paciente`, `recepcion`, `odontologo`, header con usuario y logout).
- **Infraestructura de Testing**: Configuración de Vitest + React Testing Library para tests unitarios y de integración de componentes y cliente HTTP.

## Capabilities

### New Capabilities
- `frontend-application-shell`: Runtime SPA de React con enrutador, layouts por rol (`AuthLayout`, `AppLayout`) y suite de primitivas UI accesibles (`Button`, `Input`, `Card`, etc.) con soporte para temas neutrales y alto contraste.
- `frontend-api-client`: Capa de transporte HTTP basada en Axios con interceptores de autorización JWT, gestión centralizada de sesión/expiración (401/403) e integración con TanStack Query.

### Modified Capabilities
<!-- No requirement changes to existing backend specs -->

## Impact
- **Código**: Nuevo directorio `frontend/` con `package.json`, `tsconfig.json`, `vite.config.ts`, `src/{components,layouts,lib,pages,services}` y `tests/`.
- **Dependencias**: React, React DOM, React Router, TanStack Query, Axios, Lucide React, Radix UI primitives, Tailwind CSS, Vitest, `@testing-library/react`.
- **APIs**: Conexión a los endpoints backend bajo `/api`.
