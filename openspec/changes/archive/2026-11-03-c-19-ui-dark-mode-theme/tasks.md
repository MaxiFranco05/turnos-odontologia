# Tasks: Dark Mode Theme Support

## 1. Tailwind & CSS Tokens Setup

- [x] 1.1 Configurar `darkMode: 'class'` en `frontend/tailwind.config.js` y agregar el bloque de tokens `.dark` en `frontend/src/index.css` con variables HSL para Midnight Obsidian/Slate (fondo profundo `222 47% 6%`, tarjetas elevadas `222 40% 10%`, textos nítidos `210 40% 98%` y acentos Teal/Cyan sin tonos IA-slop planos), verificando compilación limpia con `npm run build`.

## 2. Theme Engine (Context & Hook)

- [x] 2.1 Escribir tests unitarios para `ThemeProvider` y `useTheme` en `frontend/src/context/ThemeContext.test.tsx` (fase RED: validar alternancia light/dark, lectura/escritura en `localStorage` y fallback de sistema), verificando fallo inicial.
- [x] 2.2 Implementar `ThemeContext`, `ThemeProvider` y `useTheme` en `frontend/src/context/ThemeContext.tsx` (fase GREEN: mutación de clase `.dark` en `document.documentElement` y persistencia reactiva), verificando que los tests pasen.

## 3. Accessible Modern Theme Toggle Component

- [x] 3.1 Escribir tests para `ThemeToggle` en `frontend/src/components/ThemeToggle.test.tsx` (fase RED: verificar renderizado de switch tipo píldora moderna, iconos Sol/Luna, semántica `role="switch"`, `aria-checked`, interacción de clic y accesibilidad con teclado), verificando fallo inicial.
- [x] 3.2 Implementar el componente moderno `ThemeToggle` en `frontend/src/components/ThemeToggle.tsx` (fase GREEN: cápsula con sliding thumb animado, iconos vectoriales nítidos, microinteracción `active:scale-95` y anillo de foco accesible), verificando que los tests pasen.

## 4. Layouts Integration & System Verification

- [x] 4.1 Integrar `ThemeProvider` en `frontend/src/App.tsx` y montar `ThemeToggle` en los encabezados de `frontend/src/layouts/AppLayout.tsx` y `frontend/src/layouts/AuthLayout.tsx`, actualizando y ejecutando las pruebas de layouts para verificar presencia y funcionamiento.
- [x] 4.2 Ejecutar la suite completa de pruebas (`npm test -- --run`) y la compilación de producción de TypeScript (`npm run build`), verificando 100% de pruebas en verde y ausencia total de regresiones.

## Workflow follow-up

- Presentar los artefactos al usuario para su revisión y autorización de aplicación.
- Ejecutar `/opsx:apply c-19-ui-dark-mode-theme` bajo Strict TDD.
