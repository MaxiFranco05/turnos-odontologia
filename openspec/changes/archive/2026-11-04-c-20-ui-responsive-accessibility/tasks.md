# Tasks: Responsive Glassmorphism Navigation & High-End Visual Identity

## 1. Desktop Floating Glass Capsule Navigation
- [x] 1.1 Escribir tests unitarios en `frontend/src/layouts/Layouts.test.tsx` para la nueva cápsula de navegación flotante desktop (`glass-surface`, solapas tipo píldora por rol, estado activo y logout) (fase RED: verificar fallos esperados).
- [x] 1.2 Implementar la cápsula flotante de cristal centrada en `frontend/src/layouts/AppLayout.tsx` eliminando la barra lateral tradicional y agregando clases de cristal en `frontend/src/index.css` (fase GREEN: verificar que los tests pasen).

## 2. Mobile Floating Bottom Dock Navigation
- [x] 2.1 Escribir tests unitarios en `frontend/src/layouts/Layouts.test.tsx` para el dock móvil inferior con burbuja activa elevada y touch targets >= 44x44px (fase RED: verificar fallos esperados).
- [x] 2.2 Implementar el dock flotante móvil en `frontend/src/layouts/AppLayout.tsx` con posicionamiento en la zona del pulgar (`fixed bottom-4 inset-x-4`) y padding inferior de seguridad en el contenedor principal (fase GREEN: verificar que los tests pasen).

## 3. High-End Clinical Auth & Login Redesign
- [x] 3.1 Escribir tests unitarios en `frontend/src/pages/LoginPage.test.tsx` y `frontend/src/layouts/Layouts.test.tsx` para la nueva tarjeta de login con chips de acceso rápido de demostración (fase RED: verificar fallos esperados).
- [x] 3.2 Implementar el rediseño en `frontend/src/layouts/AuthLayout.tsx` y `frontend/src/pages/LoginPage.tsx` con tarjeta de cristal esmerilado, aura de luz dental sutil y chips de autocompletado para Recepción, Odontólogo y Paciente (fase GREEN: verificar que los tests pasen).

## 4. Verification & Polish
- [x] 4.1 Correr la suite completa de pruebas de frontend (`npm test -- --run`) y verificar 100% de tests en verde.
- [x] 4.2 Ejecutar `npm run build` para asegurar compilación estricta de TypeScript y bundle de producción limpio.
